"""
Application State - Singleton
מחזיק את כל ה-services המשותפים
"""

import logging
import os
from typing import Optional, Dict

from app.core.simulated_graphiti import SimulatedGraphitiClient
from app.core.simulated_llm import SimulatedLLMProvider

logger = logging.getLogger(__name__)

class AppState:
    """Application state singleton"""

    def __init__(self):
        self.graphiti: Optional[SimulatedGraphitiClient] = None
        self.llm: Optional[SimulatedLLMProvider] = None
        self.initialized = False

        # In-memory sessions storage
        # family_id -> {interview_messages, current_stage, etc.}
        self.sessions: Dict[str, Dict] = {}

    async def initialize(self):
        """אתחול כל ה-services"""
        if self.initialized:
            return

        logger.info("Initializing app state...")

        # 1. Simulated Graphiti
        self.graphiti = SimulatedGraphitiClient()
        await self.graphiti.initialize()

        # 2. Simulated LLM
        self.llm = SimulatedLLMProvider()
        logger.info("Using simulated LLM (no API calls)")

        self.initialized = True
        logger.info("✅ App state initialized")

    async def shutdown(self):
        """סגירה"""
        if self.graphiti:
            await self.graphiti.close()

        logger.info("App state shut down")

    def get_or_create_session(self, family_id: str) -> Dict:
        """קבל או צור session למשפחה"""
        if family_id not in self.sessions:
            self.sessions[family_id] = {
                "family_id": family_id,
                "current_stage": "welcome",
                "interview_messages": [],
                "child_uuid": f"child_{family_id}",
                "parent_name": "הורה",
                "videos": [],
                "created_at": None
            }

        return self.sessions[family_id]

# Singleton instance
app_state = AppState()
