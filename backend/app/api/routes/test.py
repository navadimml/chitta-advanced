"""
Test API Routes - Test mode and dev endpoints

Includes:
- /test/* - Parent simulator for testing
- /dev/* - Development/debugging utilities
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from app.core.app_state import app_state
from app.services.parent_simulator import get_parent_simulator
from app.services.unified_state_service import get_unified_state_service
from app.services.session_service import get_session_service

router = APIRouter(tags=["test"])
logger = logging.getLogger(__name__)


# === Request Models ===

class StartTestRequest(BaseModel):
    """Request to start test mode"""
    persona_id: str
    family_id: Optional[str] = None


class GenerateResponseRequest(BaseModel):
    """Request to generate parent response"""
    family_id: str
    chitta_question: str


class StopTestRequest(BaseModel):
    """Request to stop test mode"""
    family_id: str


# === Test Mode Endpoints (Parent Simulator) ===

@router.get("/test/personas")
async def list_test_personas():
    """
    List available parent personas for testing.
    Each persona represents a realistic test case.
    """
    simulator = get_parent_simulator()
    return {
        "personas": simulator.list_personas()
    }


@router.post("/test/start")
async def start_test_mode(request: StartTestRequest):
    """
    Start test mode with a parent persona.
    System will simulate this parent interacting with real backend.
    """
    simulator = get_parent_simulator()

    existing_family_id = simulator.get_active_simulation_for_persona(request.persona_id)

    if existing_family_id:
        family_id = existing_family_id
        logger.info(f"Reusing existing simulation for {request.persona_id}: {family_id}")
    else:
        family_id = request.family_id or f"test_{request.persona_id}_{int(datetime.now().timestamp())}"
        logger.info(f"Creating new simulation for {request.persona_id}: {family_id}")

    try:
        result = simulator.start_simulation(request.persona_id, family_id)

        return {
            "success": True,
            "family_id": family_id,
            "persona": result["persona"],
            "message": f"Test mode started with persona: {result['persona']['parent_name']}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/test/generate-response")
async def generate_parent_response(request: GenerateResponseRequest):
    """
    Generate realistic parent response using LLM.
    The LLM acts as the parent persona.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    simulator = get_parent_simulator()
    state_service = get_unified_state_service()

    from app.services.llm.factory import create_llm_provider
    test_llm = create_llm_provider(provider_type="gemini", model="gemini-flash-lite-latest")
    logger.info("Using gemini-flash-lite for test parent simulation")

    try:
        response = await simulator.generate_response(
            family_id=request.family_id,
            chitta_question=request.chitta_question,
            llm_provider=test_llm,
            state_service=state_service
        )

        if response is None:
            return {
                "parent_response": "",
                "interview_complete": True,
                "conversation_ended": True
            }

        return {
            "parent_response": response,
            "interview_complete": False
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating parent response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate response")


@router.post("/test/stop")
async def stop_test_mode(request: StopTestRequest):
    """
    Stop an active test simulation.
    This clears the simulation from memory.
    """
    simulator = get_parent_simulator()

    try:
        simulator.stop_simulation(request.family_id)
        logger.info(f"Stopped simulation for {request.family_id}")

        return {
            "success": True,
            "message": f"Test simulation stopped for {request.family_id}"
        }
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop simulation")


# === Dev Endpoints ===

@router.get("/dev/export-artifacts/{family_id}")
async def export_artifacts(family_id: str):
    """
    Export all artifacts for a family to JSON files for inspection.
    Files are saved to backend/artifacts_export/{family_id}/
    """
    import json
    from pathlib import Path

    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    export_dir = Path(f"artifacts_export/{family_id}")
    export_dir.mkdir(parents=True, exist_ok=True)

    exported_files = []

    for artifact_id, artifact in session.artifacts.items():
        artifact_data = {
            "artifact_id": artifact_id,
            "status": artifact.status,
            "content": artifact.content,
            "error_message": artifact.error_message,
            "created_at": str(artifact.created_at) if hasattr(artifact, 'created_at') else None,
        }

        file_path = export_dir / f"{artifact_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, ensure_ascii=False, indent=2)

        exported_files.append(str(file_path))
        logger.info(f"Exported {artifact_id} to {file_path}")

    return {
        "success": True,
        "family_id": family_id,
        "artifacts_exported": len(exported_files),
        "export_directory": str(export_dir.absolute()),
        "files": exported_files
    }
