"""
Mood system module for Generative Agents.

This module centralizes:
- Mood state storage
- Personality-based mood baseline derivation
- Event-based mood updates
- Mean-reversion drift toward baseline
- Mood history tracking
- Human-readable mood labels

Behavior is preserved from the original implementation that previously lived
across scratch.py and perceive.py.
"""

from typing import Dict, List, Optional, Tuple


class MoodManager:
    """Encapsulates mood-related state and update logic for a persona."""

    def __init__(self, innate_traits: Optional[str] = None):
        # Current mood: -1.0 (very negative) to +1.0 (very positive)
        self.mood: float = 0.0
        # Personality-based default mood that agent drifts toward
        self.mood_baseline: float = 0.0
        # History for dashboard plotting: [[HH:MM, mood], ...]
        self.mood_history: List[List[object]] = []
        # Number of conversations today
        self.convo_count_today: int = 0
        # Relationship scores with other agents
        self.relationship_scores: Dict[str, float] = {}

        if innate_traits:
            self.mood_baseline = self.derive_baseline_from_innate(innate_traits)
            self.mood = self.mood_baseline

    @staticmethod
    def clamp(value: float, min_value: float = -1.0, max_value: float = 1.0) -> float:
        """Clamp a numeric value to [min_value, max_value]."""
        return max(min_value, min(max_value, value))

    @staticmethod
    def derive_baseline_from_innate(innate_traits: str) -> float:
        """
        Derive mood baseline from innate traits.
        Preserves existing logic from scratch.py.
        """
        positive_traits = [
            "cheerful", "friendly", "optimistic", "warm", "kind",
            "energetic", "enthusiastic", "happy", "outgoing", "curious"
        ]
        negative_traits = [
            "anxious", "pessimistic", "grumpy", "shy", "reserved",
            "moody", "melancholic", "serious", "cautious", "stressed", "Hurt"
        ]

        innate_lower = innate_traits.lower()
        pos_count = sum(1 for t in positive_traits if t in innate_lower)
        neg_count = sum(1 for t in negative_traits if t in innate_lower)
        return MoodManager.clamp((pos_count - neg_count) * 0.15)

    def load_from_scratch(self, scratch_load: Dict, innate_traits: Optional[str] = None) -> None:
        """
        Load mood fields from saved scratch JSON.
        Preserves backward compatibility with existing saves.
        """
        self.mood = scratch_load.get("mood", 0.0)
        self.mood_baseline = scratch_load.get("mood_baseline", 0.0)
        self.mood_history = scratch_load.get("mood_history", [])
        self.convo_count_today = scratch_load.get("convo_count_today", 0)
        self.relationship_scores = scratch_load.get("relationship_scores", {})

        # Preserve original behavior:
        # if innate exists, derive baseline and initialize mood only for first-ever init
        if innate_traits:
            derived_baseline = self.derive_baseline_from_innate(innate_traits)
            self.mood_baseline = derived_baseline
            if "mood" not in scratch_load:
                self.mood = self.mood_baseline

    def dump_to_scratch(self, scratch: Dict) -> None:
        """Write mood fields back to scratch JSON dict."""
        scratch["mood"] = self.mood
        scratch["mood_baseline"] = self.mood_baseline
        scratch["mood_history"] = self.mood_history
        scratch["convo_count_today"] = self.convo_count_today
        scratch["relationship_scores"] = self.relationship_scores

    def update_from_events(self, event_descriptions: List[str], curr_time=None) -> None:
        """
        Update mood using event keyword heuristics + baseline drift.
        Preserves behavior from perceive.py.
        """
        mood_delta = 0.0

        for desc in event_descriptions:
            desc_lower = desc.lower()

            # Positive event keywords boost mood
            if any(w in desc_lower for w in [
                "enjoying", "finished", "completed", "happy",
                "laughing", "celebrating", "love"
            ]):
                mood_delta += 0.05

            # Negative event keywords lower mood
            elif any(w in desc_lower for w in [
                "failed", "frustrated", "stressed", "lost",
                "crying", "worried", "sick"
            ]):
                mood_delta -= 0.05

        # Natural drift back toward baseline (mean reversion)
        drift = 0.02 * (self.mood_baseline - self.mood)

        # Apply clamped update
        self.mood = self.clamp(self.mood + mood_delta + drift)

        # Record mood history
        if curr_time:
            self.mood_history.append([curr_time.strftime("%H:%M"), round(self.mood, 3)])
            # Keep only last 500 entries
            if len(self.mood_history) > 500:
                self.mood_history = self.mood_history[-500:]

    def get_mood_label(self) -> str:
        """Return human-readable mood label used in prompt identity string."""
        if self.mood > 0.5:
            return "very happy and energetic"
        if self.mood > 0.2:
            return "in a good mood"
        if self.mood > 0.05:
            return "slightly cheerful"
        if self.mood < -0.5:
            return "very stressed and unhappy"
        if self.mood < -0.2:
            return "feeling down"
        if self.mood < -0.05:
            return "slightly low"
        return "neutral"

    def get_reflection_mood_factor(self) -> float:
        """
        Mood factor used in reflection triggering logic.
        Preserves reflect.py behavior: 1.0 - (mood * 0.3)
        """
        return 1.0 - (self.mood * 0.3)
