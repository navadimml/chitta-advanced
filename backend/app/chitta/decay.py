"""
Decay Manager - Time-Based Pull Decay

מינימום המורכבות הנדרשת - minimum NECESSARY complexity.

This module handles the ONLY mechanical operation the system performs
automatically: time-based pull decay. All other changes come from LLM decisions.

CRITICAL DISTINCTION:
- PULL decays over time (mechanical, automatic)
- FULLNESS/CONFIDENCE do NOT decay (only changed by LLM with reasoning)

Pull represents "how much attention should we give this now?"
Fullness/Confidence represent "how much do we know/believe?"

A curiosity can have:
- High fullness (0.8) + low pull (0.2) = well understood, not currently active
- Low fullness (0.2) + high pull (0.8) = needs exploration, currently active

Dormancy:
- After N days without activity, curiosity becomes dormant
- Dormancy is a status change (requires event recording)
- Dormant curiosities can be revived by new relevant observations
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple

from .curiosity_types import (
    BaseCuriosity,
    Discovery,
    Question,
    Hypothesis,
    Pattern,
)


@dataclass
class DecayConfig:
    """Configuration for decay behavior."""

    # Daily decay rate per type (pull decreases by this fraction each day)
    decay_rates: dict = None

    # Days without activity before dormancy
    dormancy_days: dict = None

    def __post_init__(self):
        if self.decay_rates is None:
            self.decay_rates = {
                "discovery": 0.008,   # Discoveries decay slowly (open exploration)
                "question": 0.015,    # Questions decay faster (focused inquiry)
                "hypothesis": 0.012,  # Hypotheses decay moderately
                "pattern": 0.006,     # Patterns decay very slowly (core insights)
            }

        if self.dormancy_days is None:
            self.dormancy_days = {
                "discovery": 21,      # 3 weeks
                "question": 14,       # 2 weeks
                "hypothesis": 30,     # 1 month
                "pattern": 45,        # 1.5 months
            }


class DecayManager:
    """
    Manages time-based pull decay.

    This is the ONLY automatic/mechanical change to curiosities.
    All other changes require LLM reasoning.
    """

    def __init__(self, config: DecayConfig = None):
        """Initialize with configuration."""
        self.config = config or DecayConfig()

    def apply_decay(self, curiosity: BaseCuriosity, now: datetime = None) -> float:
        """
        Apply time-based decay to a curiosity's pull.

        Returns the amount of decay applied.

        CRITICAL: Only pull decays. Fullness/confidence are NEVER touched.
        """
        if now is None:
            now = datetime.now()

        # Get type-specific decay rate
        decay_rate = self._get_decay_rate(curiosity)

        # Calculate days since last update
        days_since_update = (now - curiosity.last_updated).total_seconds() / 86400

        if days_since_update <= 0:
            return 0.0

        # Apply exponential decay: pull = pull * (1 - rate)^days
        decay_factor = (1 - decay_rate) ** days_since_update
        old_pull = curiosity.pull
        new_pull = max(0.0, old_pull * decay_factor)

        curiosity.pull = new_pull
        return old_pull - new_pull

    def apply_decay_batch(
        self,
        curiosities: List[BaseCuriosity],
        now: datetime = None
    ) -> List[Tuple[str, float]]:
        """
        Apply decay to multiple curiosities.

        Returns list of (curiosity_id, decay_amount) for curiosities that decayed.
        """
        if now is None:
            now = datetime.now()

        results = []
        for curiosity in curiosities:
            decay_amount = self.apply_decay(curiosity, now)
            if decay_amount > 0:
                results.append((curiosity.id, decay_amount))

        return results

    def check_dormancy(self, curiosity: BaseCuriosity, now: datetime = None) -> bool:
        """
        Check if a curiosity should become dormant.

        Dormancy is triggered by:
        1. Low pull (below threshold)
        2. Days since last update exceeding dormancy threshold

        Returns True if should become dormant.
        """
        if now is None:
            now = datetime.now()

        # Already dormant statuses
        dormant_statuses = ["dormant", "dissolved", "answered", "confirmed", "refuted"]
        if curiosity.status in dormant_statuses:
            return False

        # Get type-specific dormancy threshold
        dormancy_days = self._get_dormancy_days(curiosity)

        # Calculate days since last update
        days_since_update = (now - curiosity.last_updated).total_seconds() / 86400

        # Check both conditions
        low_pull = curiosity.pull < 0.1
        long_inactive = days_since_update > dormancy_days

        return low_pull and long_inactive

    def find_dormancy_candidates(
        self,
        curiosities: List[BaseCuriosity],
        now: datetime = None
    ) -> List[BaseCuriosity]:
        """
        Find all curiosities that should become dormant.

        Returns list of curiosities ready for dormancy transition.
        """
        if now is None:
            now = datetime.now()

        candidates = []
        for curiosity in curiosities:
            if self.check_dormancy(curiosity, now):
                candidates.append(curiosity)

        return candidates

    def can_revive(self, curiosity: BaseCuriosity) -> bool:
        """
        Check if a dormant curiosity can be revived.

        Revivable statuses vary by type:
        - Discovery: dormant can be revived
        - Question: dormant can be revived (but not answered/evolved)
        - Hypothesis: dormant can be revived (but not confirmed/refuted/transformed)
        - Pattern: dissolved cannot be revived
        """
        revivable_statuses = {
            Discovery: ["dormant"],
            Question: ["dormant"],
            Hypothesis: ["dormant"],
            Pattern: ["questioned"],  # Dissolved patterns cannot be revived
        }

        curiosity_type = type(curiosity)
        return curiosity.status in revivable_statuses.get(curiosity_type, [])

    def calculate_time_to_dormancy(
        self,
        curiosity: BaseCuriosity,
        now: datetime = None
    ) -> float:
        """
        Calculate estimated days until dormancy.

        Returns days until dormancy, or -1 if already dormant or actively maintained.
        """
        if now is None:
            now = datetime.now()

        dormant_statuses = ["dormant", "dissolved", "answered", "confirmed", "refuted"]
        if curiosity.status in dormant_statuses:
            return -1

        # Get type-specific parameters
        decay_rate = self._get_decay_rate(curiosity)
        dormancy_days = self._get_dormancy_days(curiosity)

        # Calculate days until pull reaches 0.1 (dormancy threshold)
        if curiosity.pull <= 0.1:
            # Already below threshold, check time condition
            days_since_update = (now - curiosity.last_updated).total_seconds() / 86400
            remaining = dormancy_days - days_since_update
            return max(0, remaining)

        # Days until pull decays to 0.1
        # pull * (1 - rate)^days = 0.1
        # days = log(0.1/pull) / log(1-rate)
        import math
        if decay_rate >= 1:
            return 0

        days_to_low_pull = math.log(0.1 / curiosity.pull) / math.log(1 - decay_rate)
        return max(0, days_to_low_pull)

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_decay_rate(self, curiosity: BaseCuriosity) -> float:
        """Get the decay rate for a curiosity's type."""
        if isinstance(curiosity, Discovery):
            return self.config.decay_rates["discovery"]
        elif isinstance(curiosity, Question):
            return self.config.decay_rates["question"]
        elif isinstance(curiosity, Hypothesis):
            return self.config.decay_rates["hypothesis"]
        elif isinstance(curiosity, Pattern):
            return self.config.decay_rates["pattern"]
        return 0.01  # Default

    def _get_dormancy_days(self, curiosity: BaseCuriosity) -> int:
        """Get the dormancy threshold for a curiosity's type."""
        if isinstance(curiosity, Discovery):
            return self.config.dormancy_days["discovery"]
        elif isinstance(curiosity, Question):
            return self.config.dormancy_days["question"]
        elif isinstance(curiosity, Hypothesis):
            return self.config.dormancy_days["hypothesis"]
        elif isinstance(curiosity, Pattern):
            return self.config.dormancy_days["pattern"]
        return 21  # Default: 3 weeks
