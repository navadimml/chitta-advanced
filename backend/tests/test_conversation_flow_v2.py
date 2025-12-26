"""
Test V2 Curiosity Architecture integration with conversation flow.

This test verifies:
1. Darshan creation with V2 CuriosityManager
2. Message processing creates/updates V2 curiosities
3. Serialization roundtrip preserves curiosity state
4. Context formatting works with V2 types

Run: PYTHONPATH=. pytest tests/test_conversation_flow_v2.py -v -s
"""

import pytest
import asyncio
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

# Test environment setup
import os
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"


class TestV2CuriosityIntegration:
    """Test V2 curiosity architecture integration with conversation flow."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response factory."""
        from app.services.llm.base import LLMResponse, FunctionCall

        def create_response(
            function_calls: List[Dict[str, Any]] = None,
            content: str = ""
        ) -> LLMResponse:
            calls = []
            if function_calls:
                for fc in function_calls:
                    calls.append(FunctionCall(name=fc["name"], arguments=fc["args"]))
            return LLMResponse(content=content, function_calls=calls)

        return create_response

    @pytest.fixture
    def darshan(self):
        """Create a fresh Darshan instance for testing."""
        from app.chitta.gestalt import Darshan
        from app.chitta.models import Understanding

        return Darshan(
            child_id="test-child-123",
            child_name="דניאל",
            understanding=Understanding(),
            stories=[],
            journal=[],
            session_history=[],
            child_birth_date=date(2021, 6, 15),
            child_gender="male",
        )

    def test_darshan_has_curiosity_manager(self, darshan):
        """Test that Darshan uses V2 CuriosityManager."""
        from app.chitta.curiosity_manager import CuriosityManager

        # Check _curiosity_manager exists
        assert hasattr(darshan, "_curiosity_manager")
        assert isinstance(darshan._curiosity_manager, CuriosityManager)

        # Check _curiosities alias works
        assert darshan._curiosities is darshan._curiosity_manager

    def test_empty_curiosity_manager(self, darshan):
        """Test empty curiosity manager methods."""
        # get_all returns empty list
        assert darshan._curiosities.get_all() == []

        # get_hypotheses returns empty list
        assert darshan._curiosities.get_hypotheses() == []

        # get_investigating returns empty list
        assert darshan._curiosities.get_investigating() == []

        # get_video_suggestable returns empty list
        assert darshan._curiosities.get_video_suggestable() == []

        # get_active returns empty list
        assert darshan.get_active_curiosities() == []

    def test_add_hypothesis_via_tool_handler(self, darshan):
        """Test adding a hypothesis via _handle_wonder (simulating Phase 1)."""
        # Simulate the tool call args from Phase 1 perception
        wonder_args = {
            "focus": "קושי במעברים",
            "type": "hypothesis",
            "theory": "יכול להיות שמעברים קשים לדניאל כי השינוי מרגיש גדול",
            "domain": "behavioral",
            "fullness_or_confidence": 0.4,
            "assessment_reasoning": "Parent mentioned difficulty with transitions",
            "video_appropriate": True,
        }

        # Call the handler directly (as Phase 1 would)
        darshan._handle_wonder(wonder_args)

        # Verify hypothesis was created
        hypotheses = darshan._curiosities.get_hypotheses()
        assert len(hypotheses) == 1

        h = hypotheses[0]
        assert h.focus == "קושי במעברים"
        assert h.confidence == 0.4
        assert h.video_appropriate is True
        assert h.status == "weak"  # Default for confidence < 0.5

        # Verify it's in get_all
        all_curiosities = darshan._curiosities.get_all()
        assert len(all_curiosities) == 1

    def test_add_question_via_tool_handler(self, darshan):
        """Test adding a question via _handle_wonder."""
        wonder_args = {
            "focus": "איך דניאל מגיב לשינויים בשגרה",
            "type": "question",
            "question": "מה קורה כשיש שינוי בלוח הזמנים?",
            "domain": "behavioral",
            "fullness_or_confidence": 0.3,
            "assessment_reasoning": "Need more info about routine changes",
        }

        darshan._handle_wonder(wonder_args)

        # Verify question was created
        all_curiosities = darshan._curiosities.get_all()
        assert len(all_curiosities) == 1

        q = all_curiosities[0]
        from app.chitta.curiosity_types import Question
        assert isinstance(q, Question)
        assert q.focus == "איך דניאל מגיב לשינויים בשגרה"
        assert q.fullness == 0.3

    def test_add_discovery_via_tool_handler(self, darshan):
        """Test adding a discovery via _handle_wonder."""
        wonder_args = {
            "focus": "מי זה דניאל",
            "type": "discovery",
            "domain": "essence",
            "fullness_or_confidence": 0.2,
            "assessment_reasoning": "Starting to understand who Daniel is",
        }

        darshan._handle_wonder(wonder_args)

        # Verify discovery was created
        all_curiosities = darshan._curiosities.get_all()
        assert len(all_curiosities) == 1

        d = all_curiosities[0]
        from app.chitta.curiosity_types import Discovery
        assert isinstance(d, Discovery)
        assert d.focus == "מי זה דניאל"
        assert d.fullness == 0.2

    def test_add_pattern_via_tool_handler(self, darshan):
        """Test adding a pattern via _handle_wonder."""
        wonder_args = {
            "focus": "קשר בין רגישות חושית לקושי במעברים",
            "type": "pattern",
            "fullness_or_confidence": 0.5,
            "domains_involved": ["sensory", "behavioral"],
            "source_hypotheses": ["קושי במעברים"],
            "insight": "רגישות חושית גורמת לקושי במעברים",
            "assessment_reasoning": "Cross-domain connection observed",
        }

        darshan._handle_wonder(wonder_args)

        # Verify pattern was created
        all_curiosities = darshan._curiosities.get_all()
        assert len(all_curiosities) == 1

        p = all_curiosities[0]
        from app.chitta.curiosity_types import Pattern
        assert isinstance(p, Pattern)
        assert p.focus == "קשר בין רגישות חושית לקושי במעברים"
        assert p.confidence == 0.5
        assert p.domains_involved == ["sensory", "behavioral"]

    def test_add_evidence_updates_confidence(self, darshan):
        """Test adding evidence updates hypothesis confidence."""
        # First add a hypothesis
        darshan._handle_wonder({
            "focus": "קושי במעברים",
            "type": "hypothesis",
            "theory": "מעברים קשים",
            "domain": "behavioral",
            "fullness_or_confidence": 0.4,
            "assessment_reasoning": "Initial observation",
        })

        # Now add supporting evidence
        darshan._handle_add_evidence({
            "curiosity_focus": "קושי במעברים",
            "effect": "supports",
            "new_confidence": 0.6,
            "effect_reasoning": "Story confirmed the pattern",
            "source_observation": "Parent described transition meltdown",
        })

        # Verify confidence updated
        h = darshan._curiosities.get_hypotheses()[0]
        assert h.confidence == 0.6

    def test_notice_creates_observation(self, darshan):
        """Test that notice tool creates observations."""
        darshan._handle_notice({
            "observation": "דניאל רגיש לרעשים חזקים",
            "domain": "sensory",
            "confidence": 0.8,
        })

        # Verify observation was added
        assert len(darshan.understanding.observations) == 1
        obs = darshan.understanding.observations[0]
        assert obs.content == "דניאל רגיש לרעשים חזקים"
        assert obs.domain == "sensory"
        assert obs.confidence == 0.8

    def test_capture_story_creates_story(self, darshan):
        """Test that capture_story tool creates stories."""
        darshan._handle_capture_story({
            "summary": "אתמול דניאל התפרץ כשצריך היה לצאת מהבית",
            "reveals": ["קושי במעברים", "קושי בוויסות רגשי"],
            "domains": ["behavioral", "emotional"],
            "significance": 0.8,
        })

        # Verify story was added
        assert len(darshan.stories) == 1
        story = darshan.stories[0]
        assert story.summary == "אתמול דניאל התפרץ כשצריך היה לצאת מהבית"
        assert story.domains == ["behavioral", "emotional"]

        # Verify journal entry created
        assert len(darshan.journal) >= 1

    def test_serialization_roundtrip(self, darshan):
        """Test that V2 curiosities survive serialization roundtrip."""
        from app.chitta.gestalt import Darshan
        from app.chitta.curiosity_types import Hypothesis, Question, Discovery, Pattern

        # Add various curiosities
        darshan._handle_wonder({
            "focus": "קושי במעברים",
            "type": "hypothesis",
            "theory": "מעברים קשים",
            "domain": "behavioral",
            "fullness_or_confidence": 0.6,
            "assessment_reasoning": "Test hypothesis",
            "video_appropriate": True,
        })

        darshan._handle_wonder({
            "focus": "איך דניאל מגיב",
            "type": "question",
            "question": "מה קורה כשיש שינוי?",
            "domain": "behavioral",
            "fullness_or_confidence": 0.4,
            "assessment_reasoning": "Test question",
        })

        # Add observation
        darshan._handle_notice({
            "observation": "רגיש לרעשים",
            "domain": "sensory",
            "confidence": 0.9,
        })

        # Get state for persistence
        state = darshan.get_state_for_persistence()

        # Verify curiosity_manager is in state
        assert "curiosity_manager" in state
        cm_data = state["curiosity_manager"]
        assert "hypotheses" in cm_data
        assert len(cm_data["hypotheses"]) == 1

        # Reconstruct Darshan from state
        restored = Darshan.from_child_data(
            child_id=darshan.child_id,
            child_name=darshan.child_name,
            understanding_data=state.get("understanding"),
            curiosity_manager_data=state.get("curiosity_manager"),
            session_history_data=state.get("session_history"),
            child_birth_date=darshan.child_birth_date,
            child_gender=darshan.child_gender,
        )

        # Verify curiosities restored
        assert len(restored._curiosities.get_all()) == 2

        # Verify hypothesis restored correctly
        hypotheses = restored._curiosities.get_hypotheses()
        assert len(hypotheses) == 1
        h = hypotheses[0]
        assert h.focus == "קושי במעברים"
        assert h.confidence == 0.6
        assert isinstance(h, Hypothesis)

        # Verify observations restored
        assert len(restored.understanding.observations) == 1
        assert restored.understanding.observations[0].content == "רגיש לרעשים"

    def test_context_formatting_with_v2(self, darshan):
        """Test that context formatting works with V2 curiosities."""
        from app.chitta.formatting import format_curiosities

        # Add various curiosities
        darshan._handle_wonder({
            "focus": "קושי במעברים",
            "type": "hypothesis",
            "theory": "מעברים קשים",
            "domain": "behavioral",
            "fullness_or_confidence": 0.6,
            "assessment_reasoning": "Test",
        })

        darshan._handle_wonder({
            "focus": "מי זה דניאל",
            "type": "discovery",
            "domain": "essence",
            "fullness_or_confidence": 0.3,
            "assessment_reasoning": "Test",
        })

        # Get active curiosities
        active = darshan.get_active_curiosities()
        assert len(active) >= 1

        # Test formatting doesn't crash
        formatted = format_curiosities(active)
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    @pytest.mark.asyncio
    async def test_full_message_processing_with_mock(self, darshan, mock_llm_response):
        """Test full message processing with mocked LLM."""
        # Mock the LLM provider
        mock_llm = AsyncMock()

        # Phase 1: Return tool calls for perception
        phase1_response = mock_llm_response(
            function_calls=[
                {
                    "name": "notice",
                    "args": {
                        "observation": "דניאל מתקשה במעברים",
                        "domain": "behavioral",
                        "confidence": 0.8,
                    }
                },
                {
                    "name": "wonder",
                    "args": {
                        "focus": "קושי במעברים",
                        "type": "hypothesis",
                        "theory": "מעברים קשים לדניאל",
                        "domain": "behavioral",
                        "fullness_or_confidence": 0.5,
                        "assessment_reasoning": "Parent shared difficulty",
                    }
                }
            ]
        )

        # Phase 2: Return text response
        phase2_response = mock_llm_response(
            content="שמתי לב שיש קושי במעברים. ספרי לי עוד על זה."
        )

        # Make LLM return different responses for each phase
        mock_llm.chat = AsyncMock(side_effect=[phase1_response, phase2_response])

        # Patch the LLM creation
        with patch.object(darshan, '_get_llm', return_value=mock_llm):
            response = await darshan.process_message(
                "דניאל מאוד מתקשה כשצריך לצאת מהבית בבוקר"
            )

        # Verify response
        assert response.text == "שמתי לב שיש קושי במעברים. ספרי לי עוד על זה."

        # Verify observation was created
        assert len(darshan.understanding.observations) == 1
        assert darshan.understanding.observations[0].content == "דניאל מתקשה במעברים"

        # Verify hypothesis was created
        hypotheses = darshan._curiosities.get_hypotheses()
        assert len(hypotheses) == 1
        assert hypotheses[0].focus == "קושי במעברים"

        # Verify session history updated
        assert len(darshan.session_history) == 2
        assert darshan.session_history[0].role == "user"
        assert darshan.session_history[1].role == "assistant"

        # Verify cognitive turn created
        assert len(darshan.cognitive_turns) == 1
        turn = darshan.cognitive_turns[0]
        assert turn.parent_message == "דניאל מאוד מתקשה כשצריך לצאת מהבית בבוקר"
        assert len(turn.tool_calls) == 2

    def test_get_investigating_returns_hypotheses_with_investigation(self, darshan):
        """Test get_investigating only returns hypotheses with active investigations."""
        from app.chitta.curiosity_types import Hypothesis

        # Add hypothesis without investigation
        darshan._handle_wonder({
            "focus": "קושי במעברים",
            "type": "hypothesis",
            "theory": "מעברים קשים",
            "domain": "behavioral",
            "fullness_or_confidence": 0.4,
            "assessment_reasoning": "Test",
        })

        # get_investigating should be empty (no investigation started)
        assert len(darshan._curiosities.get_investigating()) == 0

        # Start investigation on the hypothesis
        h = darshan._curiosities.get_hypotheses()[0]
        h.start_investigation()

        # Now get_investigating should return it
        investigating = darshan._curiosities.get_investigating()
        assert len(investigating) == 1
        assert investigating[0].focus == "קושי במעברים"

    def test_get_video_suggestable(self, darshan):
        """Test get_video_suggestable returns appropriate hypotheses."""
        # Add video-appropriate hypothesis
        darshan._handle_wonder({
            "focus": "קושי במעברים",
            "type": "hypothesis",
            "theory": "מעברים קשים",
            "domain": "behavioral",
            "fullness_or_confidence": 0.4,
            "video_appropriate": True,
            "assessment_reasoning": "Test",
        })

        # Should be video-suggestable
        suggestable = darshan._curiosities.get_video_suggestable()
        assert len(suggestable) == 1

        # Mark as video_requested
        h = darshan._curiosities.get_hypotheses()[0]
        h.video_requested = True

        # Should no longer be suggestable
        suggestable = darshan._curiosities.get_video_suggestable()
        assert len(suggestable) == 0

    def test_cards_derive_with_v2(self, darshan):
        """Test that CardsService works with V2 curiosities."""
        from app.chitta.cards import CardsService

        cards_service = CardsService()

        # Initially no cards
        cards = cards_service.derive_cards(darshan)

        # With empty curiosities, should check for baseline video suggestion
        # (depending on message count)

        # Add a video-appropriate hypothesis
        darshan._handle_wonder({
            "focus": "קושי במעברים",
            "type": "hypothesis",
            "theory": "מעברים קשים",
            "domain": "behavioral",
            "fullness_or_confidence": 0.4,
            "video_appropriate": True,
            "assessment_reasoning": "Test",
        })

        # Cards should derive without error
        cards = cards_service.derive_cards(darshan)
        # The video suggestion card should appear if conditions match
        # (video_appropriate, not video_requested, confidence < 0.7)


class TestCuriosityManagerMethods:
    """Test CuriosityManager methods directly."""

    @pytest.fixture
    def manager(self):
        """Create a fresh CuriosityManager."""
        from app.chitta.curiosity_manager import CuriosityManager
        return CuriosityManager()

    def test_add_hypothesis(self, manager):
        """Test adding a hypothesis."""
        from app.chitta.curiosity_types import Hypothesis

        h = Hypothesis.create(
            focus="test focus",
            domain="behavioral",
            confidence=0.5,
            reasoning="test reasoning",
            theory="test theory",
        )
        manager.add(h)

        assert len(manager.get_hypotheses()) == 1
        assert manager.get_by_focus("test focus") == h

    def test_add_question(self, manager):
        """Test adding a question."""
        from app.chitta.curiosity_types import Question

        q = Question.create(
            focus="test question",
            domain="behavioral",
            fullness=0.3,
            reasoning="test reasoning",
            question="What about this?",
        )
        manager.add(q)

        assert len(manager.get_by_type("question")) == 1
        assert manager.get_by_focus("test question") == q

    def test_add_discovery(self, manager):
        """Test adding a discovery."""
        from app.chitta.curiosity_types import Discovery

        d = Discovery.create(
            focus="who is this child",
            domain="essence",
            fullness=0.2,
            reasoning="test reasoning",
        )
        manager.add(d)

        assert len(manager.get_by_type("discovery")) == 1

    def test_add_pattern(self, manager):
        """Test adding a pattern."""
        from app.chitta.curiosity_types import Pattern

        p = Pattern.create(
            focus="cross-domain pattern",
            insight="Sensory and behavioral are connected",
            domains_involved=["sensory", "behavioral"],
            source_hypotheses=["hypothesis_1"],
            reasoning="test reasoning",
            confidence=0.6,
        )
        manager.add(p)

        assert len(manager.get_by_type("pattern")) == 1

    def test_serialization(self, manager):
        """Test CuriosityManager serialization."""
        from app.chitta.curiosity_types import Hypothesis, Question
        from app.chitta.curiosity_manager import CuriosityManager

        # Add mixed curiosities
        manager.add(Hypothesis.create(
            focus="h1",
            domain="behavioral",
            confidence=0.5,
            reasoning="test",
            theory="test theory",
        ))
        manager.add(Question.create(
            focus="q1",
            domain="emotional",
            fullness=0.3,
            reasoning="test",
            question="test?",
        ))

        # Serialize
        data = manager.to_dict()

        # Verify structure
        assert "hypotheses" in data
        assert "questions" in data
        assert "discoveries" in data
        assert "patterns" in data
        assert len(data["hypotheses"]) == 1
        assert len(data["questions"]) == 1

        # Deserialize
        restored = CuriosityManager.from_dict(data)

        # Verify restored correctly
        assert len(restored.get_hypotheses()) == 1
        assert len(restored.get_by_type("question")) == 1

        # Verify hypothesis data
        h = restored.get_hypotheses()[0]
        assert h.focus == "h1"
        assert h.confidence == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
