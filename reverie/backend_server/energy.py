"""
Energy level system for Generative Agents.

This module introduces a modular EnergyManager that can be integrated
into Scratch similarly to MoodManager, while preserving backward compatibility.
"""


class EnergyManager:
    """
    Manages an agent's energy state and energy-related behavior triggers.
    """

    def __init__(
        self,
        max_energy=100.0,
        low_energy_threshold=15.0,
        walking_cost_per_step=0.1,
        working_cost_per_hour=10.0,
        talking_cost_per_hour=8.0,
        eating_recovery=30.0,
        resting_recovery_per_hour=20.0,
        forced_nap_hours=2.0,
    ):
        # Core state
        self.max_energy = float(max_energy)
        self.energy = float(max_energy)
        self.energy_baseline = float(max_energy)  # wake-up baseline for current day
        self.energy_history = []

        # Config
        self.low_energy_threshold = float(low_energy_threshold)
        self.walking_cost_per_step = float(walking_cost_per_step)
        self.working_cost_per_hour = float(working_cost_per_hour)
        self.talking_cost_per_hour = float(talking_cost_per_hour)
        self.eating_recovery = float(eating_recovery)
        self.resting_recovery_per_hour = float(resting_recovery_per_hour)
        self.forced_nap_hours = float(forced_nap_hours)

    # -----------------------------
    # Persistence helpers
    # -----------------------------
    def load_from_scratch(self, scratch_load: dict):
        self.max_energy = float(scratch_load.get("max_energy", self.max_energy))
        self.energy = float(scratch_load.get("energy", self.energy))
        self.energy_baseline = float(scratch_load.get("energy_baseline", self.energy_baseline))
        self.energy_history = scratch_load.get("energy_history", [])

        self.low_energy_threshold = float(
            scratch_load.get("low_energy_threshold", self.low_energy_threshold)
        )
        self.walking_cost_per_step = float(
            scratch_load.get("walking_cost_per_step", self.walking_cost_per_step)
        )
        self.working_cost_per_hour = float(
            scratch_load.get("working_cost_per_hour", self.working_cost_per_hour)
        )
        self.talking_cost_per_hour = float(
            scratch_load.get("talking_cost_per_hour", self.talking_cost_per_hour)
        )
        self.eating_recovery = float(scratch_load.get("eating_recovery", self.eating_recovery))
        self.resting_recovery_per_hour = float(
            scratch_load.get("resting_recovery_per_hour", self.resting_recovery_per_hour)
        )
        self.forced_nap_hours = float(
            scratch_load.get("forced_nap_hours", self.forced_nap_hours)
        )

        self._clamp()

    def dump_to_scratch(self, scratch: dict):
        scratch["max_energy"] = self.max_energy
        scratch["energy"] = self.energy
        scratch["energy_baseline"] = self.energy_baseline
        scratch["energy_history"] = self.energy_history

        scratch["low_energy_threshold"] = self.low_energy_threshold
        scratch["walking_cost_per_step"] = self.walking_cost_per_step
        scratch["working_cost_per_hour"] = self.working_cost_per_hour
        scratch["talking_cost_per_hour"] = self.talking_cost_per_hour
        scratch["eating_recovery"] = self.eating_recovery
        scratch["resting_recovery_per_hour"] = self.resting_recovery_per_hour
        scratch["forced_nap_hours"] = self.forced_nap_hours

    # -----------------------------
    # Core energy model
    # -----------------------------
    def initialize_wakeup_energy(self, hours_of_sleep: float, wake_up_mood: float):
        """
        E = 0.125 × hours_of_sleep × 100 × (1 + 0.5 × wake_up_mood)

        mood expected in [-1, 1], then clamped.
        Final energy is clamped to [0, max_energy].
        """
        mood = max(-1.0, min(1.0, float(wake_up_mood)))
        sleep_h = max(0.0, float(hours_of_sleep))

        wakeup_energy = 0.125 * sleep_h * 100.0 * (1.0 + 0.5 * mood)
        wakeup_energy = max(0.0, min(self.max_energy, wakeup_energy))

        self.energy_baseline = wakeup_energy
        self.energy = wakeup_energy
        self._clamp()
        return self.energy

    def consume_walking(self, steps: float = 1.0):
        self.energy -= self.walking_cost_per_step * max(0.0, float(steps))
        self._clamp()
        return self.energy

    def consume_working(self, hours: float = 1.0):
        self.energy -= self.working_cost_per_hour * max(0.0, float(hours))
        self._clamp()
        return self.energy

    def consume_talking(self, hours: float = 1.0):
        self.energy -= self.talking_cost_per_hour * max(0.0, float(hours))
        self._clamp()
        return self.energy

    def consume_action(self, action_type: str, duration_hours: float = 0.0, steps: float = 0.0):
        """
        Unified consumption API for extensibility.
        """
        action = (action_type or "").lower()

        if action == "walking":
            return self.consume_walking(steps if steps > 0 else 1.0)
        if action == "working":
            return self.consume_working(duration_hours if duration_hours > 0 else 1.0)
        if action == "talking":
            return self.consume_talking(duration_hours if duration_hours > 0 else 1.0)

        # Unknown action: no-op by default to avoid breaking existing logic
        self._clamp()
        return self.energy

    def recover_eating(self, amount: float = None):
        self.energy += self.eating_recovery if amount is None else float(amount)
        self._clamp()
        return self.energy

    def recover_resting(self, hours: float = 1.0):
        self.energy += self.resting_recovery_per_hour * max(0.0, float(hours))
        self._clamp()
        return self.energy

    # -----------------------------
    # Override behavior helpers
    # -----------------------------
    def should_force_rest(self) -> bool:
        return self.energy < self.low_energy_threshold

    def get_forced_rest_directive(self):
        """
        Returns an action-override directive payload that planning modules can consume.
        """
        return {
            "override": True,
            "reason": "low_energy",
            "target": "home",
            "action": "nap",
            "duration_hours": self.forced_nap_hours,
        }

    def complete_forced_nap(self):
        """
        After forced nap completes, restore to wake-up baseline.
        """
        self.energy = self.energy_baseline
        self._clamp()
        return self.energy

    # -----------------------------
    # Utilities
    # -----------------------------
    def record_energy(self, timestamp_str=None):
        if timestamp_str is None:
            timestamp_str = ""
        self.energy_history.append([timestamp_str, round(self.energy, 3)])
        if len(self.energy_history) > 1000:
            self.energy_history = self.energy_history[-1000:]

    def _clamp(self):
        self.max_energy = max(1.0, float(self.max_energy))
        self.energy = max(0.0, min(self.max_energy, float(self.energy)))
        self.energy_baseline = max(0.0, min(self.max_energy, float(self.energy_baseline)))
