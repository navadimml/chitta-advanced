"""
Artifacts API Routes - Artifact management, threads, and session endpoints

Includes:
- /artifact/* - Structured artifacts and threads
- /artifacts/* - Artifact content and actions
- /thread/* - Thread conversations
- /session/* - Session artifact management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from app.core.app_state import app_state
from app.services.artifact_thread_service import get_artifact_thread_service
from app.services.session_service import get_session_service

router = APIRouter(tags=["artifacts"])
logger = logging.getLogger(__name__)


# === Request/Response Models ===

class CreateThreadRequest(BaseModel):
    """Request to create a new thread on an artifact section."""
    family_id: str
    initial_question: str
    section_title: Optional[str] = None
    section_text: Optional[str] = None


class ThreadMessageRequest(BaseModel):
    """Request to add a message to a thread."""
    family_id: str
    content: str


class ArtifactResponse(BaseModel):
    """Response model for artifact"""
    artifact_id: str
    artifact_type: str
    status: str
    content: Optional[str] = None
    content_format: str = "markdown"
    created_at: str
    ready_at: Optional[str] = None
    error_message: Optional[str] = None


class SessionArtifactsResponse(BaseModel):
    """Response model for session artifacts list"""
    family_id: str
    artifacts: List[dict]


class ArtifactActionRequest(BaseModel):
    """Request model for artifact user actions"""
    family_id: str
    action: str


# === Structured Artifact Endpoints ===

@router.get("/artifact/{artifact_id}/structured")
async def get_structured_artifact(artifact_id: str, family_id: str):
    """
    Get artifact with sections.

    Returns the artifact structured into sections with thread counts.
    Used for rendering Living Documents with thread indicators.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()
    structured = await thread_service.get_structured_artifact(family_id, artifact_id)

    if not structured:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{artifact_id}' not found or not ready"
        )

    return {
        "artifact_id": structured.artifact_id,
        "artifact_type": structured.artifact_type,
        "title": structured.title,
        "sections": [s.model_dump() for s in structured.sections],
        "total_threads": structured.total_threads,
        "sections_with_threads": structured.sections_with_threads,
        "raw_content": structured.raw_content,
        "content_format": structured.content_format
    }


@router.get("/artifact/{artifact_id}/threads")
async def get_artifact_threads(artifact_id: str, family_id: str):
    """
    Get all threads for an artifact.

    Returns thread summaries for display on the artifact.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()
    await thread_service.get_threads_for_artifact(artifact_id, family_id)
    summaries = await thread_service.get_thread_summaries(artifact_id)

    return {
        "artifact_id": artifact_id,
        "threads": [s.model_dump() for s in summaries],
        "total_threads": len(summaries)
    }


@router.post("/artifact/{artifact_id}/section/{section_id}/thread")
async def create_thread(
    artifact_id: str,
    section_id: str,
    request: CreateThreadRequest
):
    """
    Start a new thread on a section.

    Creates a new conversation thread attached to a specific section
    of an artifact. Returns the created thread with initial message.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()

    thread = await thread_service.create_thread(
        family_id=request.family_id,
        artifact_id=artifact_id,
        section_id=section_id,
        initial_question=request.initial_question,
        section_title=request.section_title,
        section_text=request.section_text
    )

    return {
        "thread_id": thread.thread_id,
        "artifact_id": artifact_id,
        "section_id": section_id,
        "messages": [m.model_dump() for m in thread.messages],
        "created_at": thread.created_at.isoformat()
    }


# === Thread Endpoints ===

@router.get("/thread/{thread_id}")
async def get_thread(thread_id: str, artifact_id: str, family_id: str):
    """
    Get a specific thread.

    Returns full thread with all messages.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()
    await thread_service.get_threads_for_artifact(artifact_id, family_id)
    thread = await thread_service.get_thread(thread_id, artifact_id)

    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    return {
        "thread_id": thread.thread_id,
        "artifact_id": thread.artifact_id,
        "section_id": thread.section_id,
        "section_title": thread.section_title,
        "section_text": thread.section_text,
        "messages": [m.model_dump() for m in thread.messages],
        "is_resolved": thread.is_resolved,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat()
    }


@router.post("/thread/{thread_id}/message")
async def add_thread_message(thread_id: str, request: ThreadMessageRequest):
    """
    Add message to thread and get AI response.

    Adds user message to thread and generates contextual AI response.
    Returns both messages.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()

    # Find the thread to get artifact_id
    artifact_id = None
    for aid, threads in thread_service._threads_cache.items():
        if threads.get_thread(thread_id):
            artifact_id = aid
            break

    if not artifact_id:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    # Add user message
    user_msg = await thread_service.add_message(
        thread_id=thread_id,
        artifact_id=artifact_id,
        role="user",
        content=request.content
    )

    if not user_msg:
        raise HTTPException(status_code=500, detail="Failed to add message")

    # Get context for AI response
    context = await thread_service.get_thread_context(
        thread_id=thread_id,
        artifact_id=artifact_id,
        family_id=request.family_id
    )

    # Generate AI response using LLM
    try:
        from app.services.llm.factory import create_llm_provider
        from app.services.llm.base import Message

        llm = create_llm_provider()
        prompt = thread_service.build_thread_prompt(context, request.content)

        response = await llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.7,
            enable_thinking=False
        )

        ai_content = response.content

        # Add AI response to thread
        ai_msg = await thread_service.add_message(
            thread_id=thread_id,
            artifact_id=artifact_id,
            role="assistant",
            content=ai_content
        )

        return {
            "user_message": user_msg.model_dump(),
            "assistant_message": ai_msg.model_dump() if ai_msg else None,
            "thread_id": thread_id
        }

    except Exception as e:
        logger.error(f"Error generating thread response: {e}", exc_info=True)
        return {
            "user_message": user_msg.model_dump(),
            "assistant_message": None,
            "error": str(e),
            "thread_id": thread_id
        }


@router.post("/thread/{thread_id}/resolve")
async def resolve_thread(thread_id: str, artifact_id: str):
    """
    Mark thread as resolved.

    User indicates they understood/got it.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()
    success = await thread_service.resolve_thread(thread_id, artifact_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    return {"success": True, "thread_id": thread_id, "resolved": True}


# === Session Artifact Endpoints ===

@router.get("/session/{family_id}/artifacts", response_model=SessionArtifactsResponse)
async def get_session_artifacts(family_id: str):
    """
    Get all artifacts for a session.

    Returns list of all artifacts (guidelines, reports, etc.) that have been
    generated for this family session.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    artifacts_list = []
    for artifact_id, artifact in session.artifacts.items():
        artifacts_list.append({
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type,
            "status": artifact.status,
            "content_format": artifact.content_format,
            "created_at": artifact.created_at.isoformat(),
            "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None,
            "exists": artifact.exists,
            "is_ready": artifact.is_ready,
            "has_error": artifact.has_error,
            "error_message": artifact.error_message
        })

    return SessionArtifactsResponse(
        family_id=family_id,
        artifacts=artifacts_list
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, family_id: str):
    """
    Get specific artifact content.

    Returns the full artifact including content if it's ready.
    Artifact IDs: baseline_video_guidelines, baseline_parent_report, etc.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    artifact = session.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{artifact_id}' not found for family {family_id}"
        )

    logger.info(
        f"API fetch artifact '{artifact_id}' for {family_id}: "
        f"status={artifact.status}, is_ready={artifact.is_ready}, "
        f"has_content={artifact.content is not None}"
    )

    return ArtifactResponse(
        artifact_id=artifact.artifact_id,
        artifact_type=artifact.artifact_type,
        status=artifact.status,
        content=artifact.content if artifact.is_ready else None,
        content_format=artifact.content_format,
        created_at=artifact.created_at.isoformat(),
        ready_at=artifact.ready_at.isoformat() if artifact.ready_at else None,
        error_message=artifact.error_message
    )


@router.post("/artifacts/{artifact_id}/action")
async def artifact_action(artifact_id: str, request: ArtifactActionRequest):
    """
    Track user actions on artifacts.

    Actions: "view", "download", "decline"
    This tracks user engagement with generated artifacts.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    session = session_service.get_or_create_session(request.family_id)

    artifact = session.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{artifact_id}' not found"
        )

    if "user_actions" not in artifact.metadata:
        artifact.metadata["user_actions"] = []

    artifact.metadata["user_actions"].append({
        "action": request.action,
        "timestamp": datetime.now().isoformat()
    })

    session.add_artifact(artifact)

    logger.info(
        f"Artifact action tracked: {request.action} on {artifact_id} "
        f"for family {request.family_id}"
    )

    return {
        "success": True,
        "artifact_id": artifact_id,
        "action": request.action,
        "tracked_at": datetime.now().isoformat()
    }
