"""
Unit tests for Curiosity Model and Engine.

Tests the activation math, evidence effects, and curiosity management.
No LLM required - pure unit tests.
"""

import pytest
from datetime import datetime, timedelta

from app.chitta.curiosity import (
    Curiosity,
    CuriosityEngine,
    create_discovery,
    create_question,
    create_hypothesis,
    create_pattern,
)
from app.chitta.models import TemporalFact, Understanding


class TestCuriosityModel:
    """Test the Curiosity dataclass."""

    def test_four_curiosity_types_supported(self):
        """All four types can be created."""
        types = ["discovery", "question", "hypothesis", "pattern"]
        for t in types:
            c = Curiosity(focus=f"test {t}", type=t, activation=0.5, certainty=0.5)
            assert c.type == t

    def test_certainty_independent_of_type(self):
        """Certainty can be any value regardless of type."""
        # Weak hypothesis
        weak_hyp = Curiosity(
            focus="test",
            type="hypothesis",
            activation=0.7,
            certainty=0.2,
            theory="A weak theory",
        )
        assert weak_hyp.certainty == 0.2

        # Strong discovery
        strong_disc = Curiosity(
            focus="test",
            type="discovery",
            activation=0.5,
            certainty=0.9,
        )
        assert strong_disc.certainty == 0.9

    def test_should_spawn_cycle(self):
        """High activation, unexplored curiosity should spawn cycle."""
        c = Curiosity(focus="test", type="question", activation=0.8, certainty=0.3)
        assert c.should_spawn_cycle() is True

        # Low activation should not spawn
        c2 = Curiosity(focus="test", type="question", activation=0.5, certainty=0.3)
        assert c2.should_spawn_cycle() is False

        # Already explored should not spawn
        c3 = Curiosity(focus="test", type="question", activation=0.8, certainty=0.3)
        c3.times_explored = 1
        assert c3.should_spawn_cycle() is False

        # Already linked to cycle should not spawn
        c4 = Curiosity(focus="test", type="question", activation=0.8, certainty=0.3)
        c4.cycle_id = "cycle_123"
        assert c4.should_spawn_cycle() is False

    def test_update_certainty_supports(self):
        """Supporting evidence increases certainty."""
        c = Curiosity(focus="test", type="hypothesis", activation=0.5, certainty=0.5)
        c.update_certainty("supports")
        assert c.certainty == pytest.approx(0.6, abs=0.01)

    def test_update_certainty_contradicts(self):
        """Contradicting evidence decreases certainty more."""
        c = Curiosity(focus="test", type="hypothesis", activation=0.5, certainty=0.5)
        c.update_certainty("contradicts")
        assert c.certainty == pytest.approx(0.35, abs=0.01)

    def test_update_certainty_transforms(self):
        """Transforming evidence resets certainty."""
        c = Curiosity(focus="test", type="hypothesis", activation=0.5, certainty=0.8)
        c.update_certainty("transforms")
        assert c.certainty == pytest.approx(0.4, abs=0.01)

    def test_update_certainty_clamped(self):
        """Certainty is clamped to 0-1."""
        c_high = Curiosity(focus="test", type="hypothesis", activation=0.5, certainty=0.95)
        c_high.update_certainty("supports")
        assert c_high.certainty == 1.0

        c_low = Curiosity(focus="test", type="hypothesis", activation=0.5, certainty=0.1)
        c_low.update_certainty("contradicts")
        assert c_low.certainty == 0.0

    def test_boost_activation(self):
        """Boosting activation increases it."""
        c = Curiosity(focus="test", type="question", activation=0.5, certainty=0.3)
        c.boost_activation(0.2)
        assert c.activation == pytest.approx(0.7, abs=0.01)

    def test_activation_clamped_to_one(self):
        """Activation cannot exceed 1.0."""
        c = Curiosity(focus="test", type="question", activation=0.9, certainty=0.3)
        c.boost_activation(0.5)
        assert c.activation == 1.0

    def test_dampen_activation(self):
        """Dampening activation decreases it."""
        c = Curiosity(focus="test", type="question", activation=0.5, certainty=0.3)
        c.dampen_activation(0.2)
        assert c.activation == pytest.approx(0.3, abs=0.01)

    def test_activation_clamped_to_zero(self):
        """Activation cannot go below 0.0."""
        c = Curiosity(focus="test", type="question", activation=0.1, certainty=0.3)
        c.dampen_activation(0.5)
        assert c.activation == 0.0

    def test_copy_creates_independent_instance(self):
        """Copy creates a fully independent copy."""
        original = Curiosity(
            focus="test",
            type="hypothesis",
            activation=0.5,
            certainty=0.5,
            domains_involved=["motor", "social"],
        )
        copy = original.copy()

        # Modify copy
        copy.activation = 0.9
        copy.domains_involved.append("cognitive")

        # Original unchanged
        assert original.activation == 0.5
        assert len(original.domains_involved) == 2


class TestCuriosityEngine:
    """Test the CuriosityEngine class."""

    def test_engine_has_five_perpetual_curiosities(self):
        """Engine initializes with 5 perpetual curiosities."""
        engine = CuriosityEngine()
        assert len(engine._perpetual) == 5

    def test_perpetual_curiosities_types(self):
        """Perpetual curiosities have correct types."""
        engine = CuriosityEngine()
        types = [c.type for c in engine._perpetual]
        assert "discovery" in types
        assert "question" in types
        assert "pattern" in types

    def test_get_active_returns_sorted_by_activation(self):
        """get_active returns curiosities sorted by activation (descending)."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(focus="low", type="question", activation=0.3, certainty=0.5))
        engine.add_curiosity(Curiosity(focus="high", type="question", activation=0.9, certainty=0.5))

        active = engine.get_active()
        activations = [c.activation for c in active]

        # Should be descending
        assert activations == sorted(activations, reverse=True)

    def test_activation_decay_over_time(self):
        """Activation decays 2% per day without activity."""
        engine = CuriosityEngine()
        curiosity = Curiosity(
            focus="test",
            type="question",
            activation=0.8,
            certainty=0.5,
            last_activated=datetime.now() - timedelta(days=5),
        )
        engine.add_curiosity(curiosity)

        # Get with activation calculation
        active = engine.get_active()
        test_curiosity = next(c for c in active if c.focus == "test")

        # Should have decayed: 0.8 - 5*0.02 = 0.7
        expected = 0.8 - 5 * 0.02
        assert test_curiosity.activation == pytest.approx(expected, abs=0.05)

    def test_high_certainty_dampens_activation(self):
        """High certainty reduces activation (we're satisfied)."""
        engine = CuriosityEngine()

        # High certainty curiosity
        high_cert = Curiosity(
            focus="high_cert",
            type="hypothesis",
            activation=0.8,
            certainty=0.9,  # > 0.7 threshold
        )
        engine.add_curiosity(high_cert)

        # Low certainty curiosity
        low_cert = Curiosity(
            focus="low_cert",
            type="hypothesis",
            activation=0.8,
            certainty=0.3,
        )
        engine.add_curiosity(low_cert)

        active = engine.get_active()
        high = next(c for c in active if c.focus == "high_cert")
        low = next(c for c in active if c.focus == "low_cert")

        # High certainty should have lower activation
        assert high.activation < low.activation

    def test_add_curiosity_no_duplicates(self):
        """Adding duplicate focus boosts existing instead of adding."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(focus="test", type="question", activation=0.5, certainty=0.3))
        engine.add_curiosity(Curiosity(focus="test", type="question", activation=0.6, certainty=0.4))

        # Should still have only 1 dynamic curiosity
        assert len(engine._dynamic) == 1
        # Activation should be boosted
        assert engine._dynamic[0].activation == pytest.approx(0.7, abs=0.01)

    def test_remove_curiosity(self):
        """Removing curiosity by focus works."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(focus="to_remove", type="question", activation=0.5, certainty=0.3))
        engine.add_curiosity(Curiosity(focus="to_keep", type="question", activation=0.5, certainty=0.3))

        engine.remove_curiosity("to_remove")

        assert len(engine._dynamic) == 1
        assert engine._dynamic[0].focus == "to_keep"

    def test_on_fact_learned_boosts_related(self):
        """Learning a fact boosts related curiosities."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(
            focus="motor skills",
            type="question",
            activation=0.5,
            certainty=0.3,
            domain="motor",
        ))

        fact = TemporalFact(content="walks well", domain="motor")
        engine.on_fact_learned(fact)

        curiosity = engine._dynamic[0]
        assert curiosity.activation > 0.5

    def test_on_evidence_added_updates_certainty(self):
        """Adding evidence updates curiosity certainty."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(
            focus="test hypothesis",
            type="hypothesis",
            activation=0.7,
            certainty=0.5,
        ))

        engine.on_evidence_added("test hypothesis", "supports")

        curiosity = engine._dynamic[0]
        assert curiosity.certainty == pytest.approx(0.6, abs=0.01)

    def test_get_gaps_returns_uncertain_active(self):
        """get_gaps returns questions from active but uncertain curiosities."""
        engine = CuriosityEngine()

        # Active and uncertain - should appear in gaps
        engine.add_curiosity(Curiosity(
            focus="gap question",
            type="question",
            activation=0.7,
            certainty=0.3,
            question="What triggers this?",
        ))

        # Active but certain - should NOT appear
        engine.add_curiosity(Curiosity(
            focus="answered",
            type="question",
            activation=0.7,
            certainty=0.8,
            question="Already answered",
        ))

        # Inactive - should NOT appear
        engine.add_curiosity(Curiosity(
            focus="inactive",
            type="question",
            activation=0.3,
            certainty=0.3,
            question="Not active enough",
        ))

        gaps = engine.get_gaps()

        assert "What triggers this?" in gaps
        assert "Already answered" not in gaps
        assert "Not active enough" not in gaps

    def test_get_hypotheses(self):
        """get_hypotheses returns only hypothesis-type curiosities."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(focus="q", type="question", activation=0.5, certainty=0.3))
        engine.add_curiosity(Curiosity(
            focus="h",
            type="hypothesis",
            activation=0.5,
            certainty=0.3,
            theory="Test theory",
        ))

        hypotheses = engine.get_hypotheses()
        assert len(hypotheses) == 1
        assert hypotheses[0].type == "hypothesis"

    def test_get_video_appropriate_hypotheses(self):
        """get_video_appropriate_hypotheses filters correctly."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(
            focus="video_ok",
            type="hypothesis",
            activation=0.5,
            certainty=0.3,
            video_appropriate=True,
        ))
        engine.add_curiosity(Curiosity(
            focus="no_video",
            type="hypothesis",
            activation=0.5,
            certainty=0.3,
            video_appropriate=False,
        ))

        video_hyps = engine.get_video_appropriate_hypotheses()
        assert len(video_hyps) == 1
        assert video_hyps[0].focus == "video_ok"

    def test_link_to_cycle(self):
        """link_to_cycle updates curiosity state."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(focus="test", type="question", activation=0.5, certainty=0.3))

        engine.link_to_cycle("test", "cycle_123")

        curiosity = engine._dynamic[0]
        assert curiosity.cycle_id == "cycle_123"
        assert curiosity.times_explored == 1

    def test_serialization_roundtrip(self):
        """Engine can be serialized and deserialized."""
        engine = CuriosityEngine()
        engine.add_curiosity(Curiosity(
            focus="test",
            type="hypothesis",
            activation=0.7,
            certainty=0.5,
            theory="Test theory",
            video_appropriate=True,
            domain="motor",
        ))

        # Serialize
        data = engine.to_dict()

        # Deserialize
        restored = CuriosityEngine.from_dict(data)

        assert len(restored._dynamic) == 1
        c = restored._dynamic[0]
        assert c.focus == "test"
        assert c.type == "hypothesis"
        assert c.theory == "Test theory"
        assert c.video_appropriate is True


class TestCuriosityFactories:
    """Test the factory functions."""

    def test_create_discovery(self):
        """create_discovery creates correct type."""
        c = create_discovery("Who is this child?", "essence")
        assert c.type == "discovery"
        assert c.domain == "essence"
        assert c.certainty == 0.1  # Low initial certainty

    def test_create_question(self):
        """create_question creates correct type."""
        c = create_question("What triggers meltdowns?", "What causes the meltdowns?", "regulation")
        assert c.type == "question"
        assert c.question == "What causes the meltdowns?"
        assert c.domain == "regulation"

    def test_create_hypothesis(self):
        """create_hypothesis creates correct type."""
        c = create_hypothesis(
            "Music regulation",
            "Music helps him regulate",
            "regulation",
            video_appropriate=True,
        )
        assert c.type == "hypothesis"
        assert c.theory == "Music helps him regulate"
        assert c.video_appropriate is True
        assert c.certainty == 0.3  # Default initial certainty

    def test_create_pattern(self):
        """create_pattern creates correct type."""
        c = create_pattern("Sensory-motor link", ["sensory", "motor"])
        assert c.type == "pattern"
        assert c.domains_involved == ["sensory", "motor"]


class TestDomainGapCounting:
    """Test the gap counting logic."""

    def test_no_understanding_returns_default_gaps(self):
        """When no understanding, returns moderate gap count."""
        engine = CuriosityEngine()
        gaps = engine._count_domain_gaps("motor", None)
        assert gaps == 3

    def test_empty_domain_has_max_gaps(self):
        """Domain with no facts has maximum gaps."""
        engine = CuriosityEngine()
        understanding = Understanding(facts=[])
        gaps = engine._count_domain_gaps("motor", understanding)
        assert gaps == 5

    def test_few_facts_has_moderate_gaps(self):
        """Domain with 1-2 facts has moderate gaps."""
        engine = CuriosityEngine()
        understanding = Understanding(facts=[
            TemporalFact(content="walks", domain="motor"),
            TemporalFact(content="runs", domain="motor"),
        ])
        gaps = engine._count_domain_gaps("motor", understanding)
        assert gaps == 3

    def test_several_facts_has_few_gaps(self):
        """Domain with 3-5 facts has few gaps."""
        engine = CuriosityEngine()
        understanding = Understanding(facts=[
            TemporalFact(content="fact1", domain="motor"),
            TemporalFact(content="fact2", domain="motor"),
            TemporalFact(content="fact3", domain="motor"),
            TemporalFact(content="fact4", domain="motor"),
        ])
        gaps = engine._count_domain_gaps("motor", understanding)
        assert gaps == 1

    def test_many_facts_has_no_gaps(self):
        """Domain with 6+ facts has no gaps."""
        engine = CuriosityEngine()
        understanding = Understanding(facts=[
            TemporalFact(content=f"fact{i}", domain="motor")
            for i in range(7)
        ])
        gaps = engine._count_domain_gaps("motor", understanding)
        assert gaps == 0
