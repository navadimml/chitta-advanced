"""
Shared request/response models for API routes.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# === UI State Models ===

class UIStateUpdate(BaseModel):
    """UI state sent with each message from frontend"""
    current_view: Optional[str] = None
    progress: Optional[dict] = None
    recent_interactions: Optional[List[str]] = None
    dismissed_cards: Optional[List[str]] = None
    expanded_cards: Optional[List[str]] = None
    current_deep_view: Optional[str] = None


# === Chat Models ===

class SendMessageRequest(BaseModel):
    family_id: str
    message: str
    parent_name: Optional[str] = "הורה"
    ui_state: Optional[UIStateUpdate] = None


class SendMessageResponse(BaseModel):
    response: str
    ui_data: dict


class SendMessageV2Request(BaseModel):
    family_id: str
    message: str
    parent_name: Optional[str] = "הורה"


class SendMessageV2Response(BaseModel):
    response: str
    curiosity_state: dict
    portrait_preview: Optional[dict] = None


class ChatV2InitResponse(BaseModel):
    family_id: str
    child_name: str
    conversation_history: list
    curiosity_state: dict
    active_cycle: Optional[dict] = None
    synthesis_available: bool = False


# === Interview Models ===

class CompleteInterviewResponse(BaseModel):
    success: bool
    video_guidelines: dict
    next_stage: str


# === Journal Models ===

class JournalEntryRequest(BaseModel):
    family_id: str
    content: str
    category: str


class JournalEntryResponse(BaseModel):
    entry_id: str
    timestamp: str
    success: bool


# === View Models ===

class AvailableViewsResponse(BaseModel):
    family_id: str
    available_views: List[str]


class ViewContentResponse(BaseModel):
    view_id: str
    view_name: str
    view_name_en: str
    available: bool
    content: Optional[dict] = None
    reason_unavailable: Optional[str] = None


# === Artifact Models ===

class ArtifactResponse(BaseModel):
    artifact_id: str
    artifact_type: str
    status: str
    content: Optional[str] = None
    content_format: str = "markdown"
    created_at: str
    ready_at: Optional[str] = None
    error_message: Optional[str] = None


class SessionArtifactsResponse(BaseModel):
    family_id: str
    artifacts: List[dict]


class ArtifactActionRequest(BaseModel):
    family_id: str
    action: str


# === Gestalt Models ===

class GestaltCardsResponse(BaseModel):
    family_id: str
    cards: List[dict]
    context: Optional[dict] = None


class CardActionRequest(BaseModel):
    family_id: str
    card_id: str
    action: str
    action_data: Optional[Dict[str, Any]] = None


class CardActionResponse(BaseModel):
    success: bool
    action: str
    result: Optional[dict] = None
    updated_cards: Optional[List[dict]] = None


class GestaltSummaryResponse(BaseModel):
    family_id: str
    child_name: str
    summary: dict
    portrait: Optional[dict] = None


class VideoInsightsResponse(BaseModel):
    family_id: str
    cycle_id: str
    insights: dict


# === Demo Mode Models ===

class DemoStartRequest(BaseModel):
    scenario_id: Optional[str] = "language_concerns"


class DemoStartResponse(BaseModel):
    demo_family_id: str
    scenario: dict
    first_message: dict
    demo_card: dict


class DemoNextResponse(BaseModel):
    step: int
    total_steps: int
    message: dict
    artifact_generated: Optional[dict] = None
    card_hint: Optional[str] = None
    demo_card: dict
    is_complete: bool


class DemoStopResponse(BaseModel):
    success: bool
    message: str


# === Test Mode Models ===

class TestStartRequest(BaseModel):
    persona_id: str
    family_id: Optional[str] = None


class TestStartResponse(BaseModel):
    family_id: str
    persona: dict
    first_message: str


class TestGenerateRequest(BaseModel):
    family_id: str
    chitta_message: str


class TestGenerateResponse(BaseModel):
    parent_response: str
    persona_state: dict


# === Child Space Models ===

class ChildSpaceResponse(BaseModel):
    family_id: str
    child_name: str
    portrait: Optional[dict] = None
    slots: List[dict]


class ShareReadinessResponse(BaseModel):
    ready: bool
    recipient_type: str
    missing_items: List[str]
    available_data: dict


class GuidedCollectionStartRequest(BaseModel):
    recipient_type: str
    focus_areas: Optional[List[str]] = None


class GuidedCollectionEndRequest(BaseModel):
    collection_id: str


class ShareGenerateRequest(BaseModel):
    recipient_type: str
    include_sections: Optional[List[str]] = None


class ShareGenerateResponse(BaseModel):
    summary_id: str
    content: str
    format: str
