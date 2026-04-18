import sys
import os

# Fix import path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../../.."))
sys.path.append(PROJECT_ROOT)

from generative_agents.reverie.backend_server.persona.memory_structures.scratch import Scratch


def main():
    print("✅ Running final test...")

    # 🔧 Minimal dummy saved state
    dummy_saved = {}

    # Create Scratch instance correctly
    s = Scratch(dummy_saved)

    # Test compatibility layer
    print("Initial mood:", s.mood)

    s.mood = 0.5
    print("Updated mood (via property):", s.mood)
    print("Manager mood:", s.mood_manager.mood)

    # Assertions
    assert s.mood == s.mood_manager.mood, "❌ Mood mismatch!"

    print("✅ Compatibility layer working correctly")
    print("🎉 All checks passed!")


if __name__ == "__main__":
    main()