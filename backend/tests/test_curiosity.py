"""
Unit tests for Curiosity Model and Curiosities.

Tests the pull math, evidence effects, and curiosity management.
No LLM required - pure unit tests.
"""

import pytest
from datetime import datetime, timedelta

from app.chitta.curiosity import (
    Curiosity,
    Curiosities,
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
            c = Curiosity(focus=f"test {t}", type=t, pull=0.5, certainty=0.5)
            assert c.type == t

    def test_certainty_independent_of_type(self):
        """Certainty can be any value regardless of type."""
        # Weak hypothesis
        weak_hyp = Curiosity(
            focus="test",
            type="hypothesis",
            pull=0.7,
            certainty=0.2,
            theory="A weak theory",
        )
        assert weak_hyp.certainty == 0.2

        # Strong discovery
        strong_disc = Curiosity(
            focus="test",
            type="discovery",
            pull=0.5,
            certainty=0.9,
        )
        assert strong_disc.certainty == 0.9

    def test_should_spawn_exploration(self):
        """High pull, unexplored curiosity should spawn exploration."""
        c = Curiosity(focus="test", type="question", pull=0.8, certainty=0.3)
        assert c.should_spawn_exploration() is True

        # Low pull should not spawn
        c2 = Curiosity(focus="test", type="question", pull=0.5, certainty=0.3)
        assert c2.should_spawn_exploration() is False

        # Already explored should not spawn
        c3 = Curiosity(focus="test", type="question", pull=0.8, certainty=0.3)
        c3.times_explored = 1
        assert c3.should_spawn_exploration() is False

        # Already linked to exploration should not spawn
        c4 = Curiosity(focus="test", type="question", pull=0.8, certainty=0.3)
        c4.cycle_id = "exploration_123"  # cycle_id is still used internally
        assert c4.should_spawn_exploration() is False

    def test_update_certainty_supports(self):
        """Supporting evidence increases certainty."""
        c = Curiosity(focus="test", type="hypothesis", pull=0.5, certainty=0.5)
        c.update_certainty("supports")
        assert c.certainty == pytest.approx(0.6, abs=0.01)

    def test_update_certainty_contradicts(self):
        """Contradicting evidence decreases certainty more."""
        c = Curiosity(focus="test", type="hypothesis", pull=0.5, certainty=0.5)
        c.update_certainty("contradicts")
        assert c.certainty == pytest.approx(0.35, abs=0.01)

    def test_update_certainty_transforms(self):
        """Transforming evidence resets certainty."""
        c = Curiosity(focus="test", type="hypothesis", pull=0.5, certainty=0.8)
        c.update_certainty("transforms")
        assert c.certainty == pytest.approx(0.4, abs=0.01)

    def test_update_certainty_clamped(self):
        """Certainty is clamped to 0-1."""
        c_high = Curiosity(focus="test", type="hypothesis", pull=0.5, certainty=0.95)
        c_high.update_certainty("supports")
        assert c_high.certainty == 1.0

        c_low = Curiosity(focus="test", type="hypothesis", pull=0.5, certainty=0.1)
        c_low.update_certainty("contradicts")
        assert c_low.certainty == 0.0

    def test_boost_pull(self):
        """Boosting pull increases it."""
        c = Curiosity(focus="test", type="question", pull=0.5, certainty=0.3)
        c.boost_pull(0.2)
        assert c.pull == pytest.approx(0.7, abs=0.01)

    def test_pull_clamped_to_one(self):
        """Pull cannot exceed 1.0."""
        c = Curiosity(focus="test", type="question", pull=0.9, certainty=0.3)
        c.boost_pull(0.5)
        assert c.pull == 1.0

    def test_dampen_pull(self):
        """Dampening pull decreases it."""
        c = Curiosity(focus="test", type="question", pull=0.5, certainty=0.3)
        c.dampen_pull(0.2)
        assert c.pull == pytest.approx(0.3, abs=0.01)

    def test_pull_clamped_to_zero(self):
        """Pull cannot go below 0.0."""
        c = Curiosity(focus="test", type="question", pull=0.1, certainty=0.3)
        c.dampen_pull(0.5)
        assert c.pull == 0.0

    def test_copy_creates_independent_instance(self):
        """Copy creates a fully independent copy."""
        original = Curiosity(
            focus="test",
            type="hypothesis",
            pull=0.5,
            certainty=0.5,
            domains_involved=["motor", "social"],
        )
        copy = original.copy()

        # Modify copy
        copy.pull = 0.9
        copy.domains_involved.append("cognitive")

        # Original unchanged
        assert original.pull == 0.5
        assert len(original.domains_involved) == 2


class TestCuriosities:
    """Test the Curiosities class."""

    def test_engine_has_perpetual_curiosities(self):
        """Engine initializes with perpetual curiosities."""
        engine = Curiosities()
        assert len(engine._perpetual) == 8

    def test_perpetual_curiosities_types(self):
        """Perpetual curiosities have correct types."""
        engine = Curiosities()
        types = [c.type for c in engine._perpetual]
        assert "discovery" in types
        assert "question" in types
        assert "pattern" in types

    def test_get_active_returns_sorted_by_activation(self):
        """get_active returns curiosities sorted by activation (descending)."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(focus="low", type="question", pull=0.3, certainty=0.5))
        engine.add_curiosity(Curiosity(focus="high", type="question", pull=0.9, certainty=0.5))

        active = engine.get_active()
        activations = [c.pull for c in active]

        # Should be descending
        assert activations == sorted(activations, reverse=True)

    def test_activation_decay_over_time(self):
        """Activation decays 2% per day without activity."""
        engine = Curiosities()
        curiosity = Curiosity(
            focus="test",
            type="question",
            pull=0.8,
            certainty=0.5,
            last_activated=datetime.now() - timedelta(days=5),
        )
        engine.add_curiosity(curiosity)

        # Get with activation calculation
        active = engine.get_active()
        test_curiosity = next(c for c in active if c.focus == "test")

        # Should have decayed: 0.8 - 5*0.02 = 0.7
        expected = 0.8 - 5 * 0.02
        assert test_curiosity.pull == pytest.approx(expected, abs=0.05)

    def test_high_certainty_dampens_activation(self):
        """High certainty reduces activation (we're satisfied)."""
        engine = Curiosities()

        # High certainty curiosity
        high_cert = Curiosity(
            focus="high_cert",
            type="hypothesis",
            pull=0.8,
            certainty=0.9,  # > 0.7 threshold
        )
        engine.add_curiosity(high_cert)

        # Low certainty curiosity
        low_cert = Curiosity(
            focus="low_cert",
            type="hypothesis",
            pull=0.8,
            certainty=0.3,
        )
        engine.add_curiosity(low_cert)

        active = engine.get_active()
        high = next(c for c in active if c.focus == "high_cert")
        low = next(c for c in active if c.focus == "low_cert")

        # High certainty should have lower activation
        assert high.pull < low.pull

    def test_add_curiosity_no_duplicates(self):
        """Adding duplicate focus boosts existing instead of adding."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(focus="test", type="question", pull=0.5, certainty=0.3))
        engine.add_curiosity(Curiosity(focus="test", type="question", pull=0.6, certainty=0.4))

        # Should still have only 1 dynamic curiosity
        assert len(engine._dynamic) == 1
        # Activation should be boosted
        assert engine._dynamic[0].pull == pytest.approx(0.7, abs=0.01)

    def test_remove_curiosity(self):
        """Removing curiosity by focus works."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(focus="to_remove", type="question", pull=0.5, certainty=0.3))
        engine.add_curiosity(Curiosity(focus="to_keep", type="question", pull=0.5, certainty=0.3))

        engine.remove_curiosity("to_remove")

        assert len(engine._dynamic) == 1
        assert engine._dynamic[0].focus == "to_keep"

    def test_on_observation_learned_boosts_related(self):
        """Learning an observation boosts related curiosities."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(
            focus="motor skills",
            type="question",
            pull=0.5,
            certainty=0.3,
            domain="motor",
        ))

        observation = TemporalFact(content="walks well", domain="motor")
        engine.on_observation_learned(observation)

        curiosity = engine._dynamic[0]
        assert curiosity.pull > 0.5

    def test_on_evidence_added_updates_certainty(self):
        """Adding evidence updates curiosity certainty."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(
            focus="test hypothesis",
            type="hypothesis",
            pull=0.7,
            certainty=0.5,
        ))

        engine.on_evidence_added("test hypothesis", "supports")

        curiosity = engine._dynamic[0]
        assert curiosity.certainty == pytest.approx(0.6, abs=0.01)

    def test_get_gaps_returns_uncertain_active(self):
        """get_gaps returns questions from active but uncertain curiosities."""
        engine = Curiosities()

        # Active and uncertain - should appear in gaps
        engine.add_curiosity(Curiosity(
            focus="gap question",
            type="question",
            pull=0.7,
            certainty=0.3,
            question="What triggers this?",
        ))

        # Active but certain - should NOT appear
        engine.add_curiosity(Curiosity(
            focus="answered",
            type="question",
            pull=0.7,
            certainty=0.8,
            question="Already answered",
        ))

        # Inactive - should NOT appear
        engine.add_curiosity(Curiosity(
            focus="inactive",
            type="question",
            pull=0.3,
            certainty=0.3,
            question="Not active enough",
        ))

        gaps = engine.get_gaps()

        assert "What triggers this?" in gaps
        assert "Already answered" not in gaps
        assert "Not active enough" not in gaps

    def test_get_hypotheses(self):
        """get_hypotheses returns only hypothesis-type curiosities."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(focus="q", type="question", pull=0.5, certainty=0.3))
        engine.add_curiosity(Curiosity(
            focus="h",
            type="hypothesis",
            pull=0.5,
            certainty=0.3,
            theory="Test theory",
        ))

        hypotheses = engine.get_hypotheses()
        assert len(hypotheses) == 1
        assert hypotheses[0].type == "hypothesis"

    def test_get_video_appropriate_hypotheses(self):
        """get_video_appropriate_hypotheses filters correctly."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(
            focus="video_ok",
            type="hypothesis",
            pull=0.5,
            certainty=0.3,
            video_appropriate=True,
        ))
        engine.add_curiosity(Curiosity(
            focus="no_video",
            type="hypothesis",
            pull=0.5,
            certainty=0.3,
            video_appropriate=False,
        ))

        video_hyps = engine.get_video_appropriate_hypotheses()
        assert len(video_hyps) == 1
        assert video_hyps[0].focus == "video_ok"

    def test_link_to_cycle(self):
        """link_to_cycle updates curiosity state."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(focus="test", type="question", pull=0.5, certainty=0.3))

        engine.link_to_cycle("test", "cycle_123")

        curiosity = engine._dynamic[0]
        assert curiosity.cycle_id == "cycle_123"  # cycle_id is still used internally
        assert curiosity.times_explored == 1

    def test_serialization_roundtrip(self):
        """Engine can be serialized and deserialized."""
        engine = Curiosities()
        engine.add_curiosity(Curiosity(
            focus="test",
            type="hypothesis",
            pull=0.7,
            certainty=0.5,
            theory="Test theory",
            video_appropriate=True,
            domain="motor",
        ))

        # Serialize
        data = engine.to_dict()

        # Deserialize
        restored = Curiosities.from_dict(data)

        assert len(restored._dynamic) == 1
        c = restored._dynamic[0]
        assert c.focus == "test"
        assert c.type == "hypothesis"
        assert c.theory == "Test theory"
        assert c.video_appropriate is True

    def test_get_curiosities_with_video_value(self):
        """get_curiosities_with_video_value filters by video_value presence."""
        engine = Curiosities()
        # Has video_value
        engine.add_curiosity(Curiosity(
            focus="calibrate eye contact",
            type="hypothesis",
            pull=0.7,
            certainty=0.3,
            video_value="calibration",
            video_value_reason="Parent said never",
        ))
        # No video_value
        engine.add_curiosity(Curiosity(
            focus="what triggers meltdowns",
            type="question",
            pull=0.7,
            certainty=0.3,
        ))
        # Has video_value (different type)
        engine.add_curiosity(Curiosity(
            focus="chain pattern",
            type="pattern",
            pull=0.6,
            certainty=0.3,
            video_value="chain",
            video_value_reason="May see sequence",
        ))

        with_video = engine.get_curiosities_with_video_value()
        assert len(with_video) == 2
        assert all(c.video_value is not None for c in with_video)

    def test_baseline_video_request_methods(self):
        """Baseline video request methods work correctly."""
        engine = Curiosities()

        # Initially not requested
        assert engine.should_suggest_baseline_video(5) is True

        # After marking as requested
        engine.mark_baseline_video_requested()
        assert engine.should_suggest_baseline_video(5) is False

    def test_baseline_video_timing(self):
        """Baseline video is only suggested at the right time."""
        engine = Curiosities()

        # Too early
        assert engine.should_suggest_baseline_video(1) is False
        assert engine.should_suggest_baseline_video(2) is False

        # Just right (messages 3-15 inclusive)
        assert engine.should_suggest_baseline_video(3) is True
        assert engine.should_suggest_baseline_video(10) is True
        assert engine.should_suggest_baseline_video(15) is True  # 15 is valid (> 15 is the cutoff)

        # Too late
        assert engine.should_suggest_baseline_video(16) is False

    def test_serialization_preserves_baseline_video_requested(self):
        """Serialization roundtrip preserves baseline_video_requested."""
        engine = Curiosities()
        engine.mark_baseline_video_requested()

        data = engine.to_dict()
        restored = Curiosities.from_dict(data)

        assert restored._baseline_video_requested is True
        assert restored.should_suggest_baseline_video(5) is False


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

    def test_create_hypothesis_with_video_value(self):
        """create_hypothesis accepts video_value and video_value_reason."""
        c = create_hypothesis(
            "Eye contact calibration",
            "He never makes eye contact",
            "social",
            video_appropriate=True,
            video_value="calibration",
            video_value_reason="Parent said 'never' - video could show the actual picture",
        )
        assert c.type == "hypothesis"
        assert c.video_value == "calibration"
        assert c.video_value_reason == "Parent said 'never' - video could show the actual picture"

    def test_create_pattern(self):
        """create_pattern creates correct type."""
        c = create_pattern("Sensory-motor link", ["sensory", "motor"])
        assert c.type == "pattern"
        assert c.domains_involved == ["sensory", "motor"]


class TestDomainGapCounting:
    """Test the gap counting logic."""

    def test_no_understanding_returns_default_gaps(self):
        """When no understanding, returns moderate gap count."""
        engine = Curiosities()
        gaps = engine._count_domain_gaps("motor", None)
        assert gaps == 3

    def test_empty_domain_has_max_gaps(self):
        """Domain with no observations has maximum gaps."""
        engine = Curiosities()
        understanding = Understanding(observations=[])
        gaps = engine._count_domain_gaps("motor", understanding)
        assert gaps == 5

    def test_few_observations_has_moderate_gaps(self):
        """Domain with 1-2 observations has moderate gaps."""
        engine = Curiosities()
        understanding = Understanding(observations=[
            TemporalFact(content="walks", domain="motor"),
            TemporalFact(content="runs", domain="motor"),
        ])
        gaps = engine._count_domain_gaps("motor", understanding)
        assert gaps == 3

    def test_several_observations_has_few_gaps(self):
        """Domain with 3-5 observations has few gaps."""
        engine = Curiosities()
        understanding = Understanding(observations=[
            TemporalFact(content="fact1", domain="motor"),
            TemporalFact(content="fact2", domain="motor"),
            TemporalFact(content="fact3", domain="motor"),
            TemporalFact(content="fact4", domain="motor"),
        ])
        gaps = engine._count_domain_gaps("motor", understanding)
        assert gaps == 1

    def test_many_observations_has_no_gaps(self):
        """Domain with 6+ observations has no gaps."""
        engine = Curiosities()
        understanding = Understanding(observations=[
            TemporalFact(content=f"fact{i}", domain="motor")
            for i in range(7)
        ])
        gaps = engine._count_domain_gaps("motor", understanding)
        assert gaps == 0
