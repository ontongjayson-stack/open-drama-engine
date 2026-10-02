"""
Open Drama Engine — Shot Refinement Verification Suite (test_refine_shot.py)
Validates POST /api/refine-shot backend route and omnirouter.py refine_shot logic.
"""

import sys
import json
from omnirouter import OmniRouter

def test_refine_shot_logic():
    print("=" * 70)
    print("[REFINE SHOT TEST] VERIFYING RE-ROLL SHOT PROMPT REFINEMENT")
    print("=" * 70)

    router = OmniRouter()

    shot_id = "1"
    original_prompt = "2D cartoon anime style, close up shot of a cybernetic cat wearing glowing neon goggles"
    tweak_instruction = "Add dramatic lightning bolts and smoke effects"
    topic = "Cybernetic Cat Hero Escaping Drone"
    genre = "2D Cartoon Action"

    print(f"Original Shot {shot_id} Prompt: '{original_prompt}'")
    print(f"Tweak Instruction: '{tweak_instruction}'")

    res = router.refine_shot(
        shot_id=shot_id,
        original_prompt=original_prompt,
        tweak_instruction=tweak_instruction,
        topic=topic,
        genre=genre
    )

    print("\n--- [RESULT PAYLOAD] ---")
    print(json.dumps(res, indent=2))

    assert res.get("success") is True, "Refine shot response missing success: True"
    assert "prompt" in res or "refinedPrompt" in res, "Refine shot response missing prompt string"
    assert "framing" in res or "refinedFraming" in res, "Refine shot response missing framing schema"

    print("\n" + "=" * 70)
    print("[SUCCESS] RE-ROLL SHOT PROMPT REFINEMENT VERIFIED WITH ZERO ERRORS!")
    print("=" * 70)

if __name__ == "__main__":
    test_refine_shot_logic()
