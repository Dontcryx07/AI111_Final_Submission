"""
Emotion contagion module for Generative Agents.

This module isolates the interpersonal mood-transfer logic used when
two agents converse. Behavior is preserved from plan.py.
"""


def apply_emotion_contagion(init_persona, target_persona, contagion_rate=0.15):
    """
    Apply emotional contagion between two personas during conversation.

    Original behavior preserved:
    - 15% of mood difference transfers both ways
    - moods clamped to [-1.0, 1.0]
    - conversation count incremented for both agents
    """

    init_mood_before = init_persona.scratch.mood
    target_mood_before = target_persona.scratch.mood

    init_persona.scratch.mood += contagion_rate * (target_mood_before - init_mood_before)
    target_persona.scratch.mood += contagion_rate * (init_mood_before - target_mood_before)

    init_persona.scratch.mood = max(-1.0, min(1.0, init_persona.scratch.mood))
    target_persona.scratch.mood = max(-1.0, min(1.0, target_persona.scratch.mood))

    init_persona.scratch.convo_count_today += 1
    target_persona.scratch.convo_count_today += 1
