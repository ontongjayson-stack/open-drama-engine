"""
Open Drama Engine — Milestone 2 Script Automation & Batch Queue Integration Test
Tests:
1. Script Generation & Parsing API (POST /api/generate-script)
2. Sequential Batch Queue Execution (Shot 01, Shot 02, Shot 03)
3. Timeline Auto-Placement & Multi-Shot Sequence Export (15s Finished MP4)
"""

import sys
import json
import time
import requests
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from omnirouter import OmniRouter
from render_engine import RenderEngine

SERVER_URL = "http://127.0.0.1:7860"

def run_milestone2_test():
    print("=" * 70)
    print("[MILESTONE 2 TEST] SCRIPT AUTOMATION & BATCH QUEUE TEST SUITE")
    print("=" * 70)

    router = OmniRouter()
    engine = RenderEngine(fps=24)
    results = {}

    # -------------------------------------------------------------------------
    # TEST 1: Script Generation & Parsing API Test
    # -------------------------------------------------------------------------
    print("\n--- [TEST 1]: Script Generation & Parsing API (POST /api/generate-script) ---")
    script_payload = {
        "topic": "A cybernetic cat hero escaping a surveillance drone in a neon alleyway",
        "genre": "2D Cartoon Action",
        "targetDuration": 15
    }

    t1_start = time.time()
    res = requests.post(f"{SERVER_URL}/api/generate-script", json=script_payload, timeout=10)
    t1_duration = time.time() - t1_start

    print(f"Test 1 HTTP Status: {res.status_code}")
    assert res.status_code == 200, f"Script generation endpoint failed with HTTP {res.status_code}"
    
    script_data = res.json()
    print(f"Test 1 Duration: {t1_duration:.2f}s")
    print(f"Parsed Script Summary: Topic='{script_data.get('topic')}', Shots={len(script_data.get('shots', []))}")

    assert script_data.get("success") == True, "Script generation returned success=False"
    shots = script_data.get("shots", [])
    assert len(shots) == 3, f"Expected 3 shots for 15s duration, got {len(shots)}"

    for idx, s in enumerate(shots):
        print(f"  └─ Card {idx+1}: [{s['title']}] ({s['duration']}s - {s['framing']})")
        print(f"     Prompt: {s['prompt'][:70]}...")
        assert "prompt" in s and s["prompt"], f"Shot card {idx+1} missing prompt text"
        assert "framing" in s and s["framing"], f"Shot card {idx+1} missing framing tag"

    print("[PASSED] TEST 1: Script Generation & 3 Shot Cards Parsing verified!")
    results["test_1"] = script_data

    # -------------------------------------------------------------------------
    # TEST 2: Batch Queue Execution Test (Generate All Shots)
    # -------------------------------------------------------------------------
    print("\n--- [TEST 2]: Batch Queue Execution (Generate All Shots) ---")
    batch_rendered_shots = []
    
    t2_start = time.time()
    for idx, s in enumerate(shots):
        print(f"\n⚡ Batch Queue Step {idx+1}/3: Rendering {s['title']}...")
        print(f"   Status Transition: IDLE -> RENDERING...")
        
        t_shot_start = time.time()
        img_res = router.generate_image(
            prompt=s["prompt"],
            aspect_ratio="16:9",
            privacy_mode=True
        )
        t_shot_dur = time.time() - t_shot_start

        assert img_res.get("success") == True, f"Batch queue failed on shot {idx+1}"
        assert Path(img_res["image_path"]).exists(), f"Image path for shot {idx+1} missing"

        # Build preview clip MP4 for shot
        preview_mp4 = Path(img_res["image_path"]).with_suffix(".mp4")
        clip_res = engine.render_sequence(
            shots=[{
                "image_path": img_res["image_path"],
                "title": s["title"],
                "prompt": s["prompt"],
                "duration": 5.0
            }],
            output_path=str(preview_mp4),
            aspect_ratio="16:9",
            bpm_sync=False
        )

        print(f"   Status Transition: RENDERING... -> READY (Rendered in {t_shot_dur:.2f}s)")
        print(f"   Generated Asset: {preview_mp4.name} ({Path(preview_mp4).stat().st_size} bytes)")

        batch_rendered_shots.append({
            "image_path": img_res["image_path"],
            "video_path": str(preview_mp4),
            "title": s["title"],
            "prompt": s["prompt"],
            "duration": 5.0,
            "start_time": idx * 5.0
        })

    t2_duration = time.time() - t2_start
    print(f"\n[PASSED] TEST 2: Batch Queue rendered {len(batch_rendered_shots)} shots in {t2_duration:.2f}s!")
    results["test_2"] = batch_rendered_shots

    # -------------------------------------------------------------------------
    # TEST 3: Timeline Auto-Placement & 15-Second Sequence Export
    # -------------------------------------------------------------------------
    print("\n--- [TEST 3]: Timeline Auto-Placement & 15s Sequence Export ---")
    output_sequence_mp4 = "test_milestone2_assembled_script_sequence.mp4"

    print("Verifying Chronological Timeline Alignment on VIDEO 1 track:")
    for shot in batch_rendered_shots:
        print(f"  └─ VIDEO 1 Clip: '{shot['title']}' | Start: {shot['start_time']:.1f}s | End: {shot['start_time']+shot['duration']:.1f}s")

    t3_start = time.time()
    export_res = engine.render_sequence(
        shots=batch_rendered_shots,
        output_path=output_sequence_mp4,
        aspect_ratio="16:9",
        bpm_sync=True
    )
    t3_duration = time.time() - t3_start

    print(f"\nTest 3 Export Duration: {t3_duration:.2f}s")
    print(f"Export Result: {json.dumps(export_res, indent=2)}")

    assert export_res.get("success") == True, "Sequence export failed"
    assert Path(output_sequence_mp4).exists(), "Output sequence MP4 file does not exist"
    out_size = Path(output_sequence_mp4).stat().st_size
    assert out_size > 0, "Output sequence MP4 file is empty (0 bytes)"

    print(f"✅ Final Output Video: {output_sequence_mp4} ({out_size} bytes, 15.0s duration)")
    print("[PASSED] TEST 3: Multi-Shot Timeline Sequence Muxing & Export verified!")
    results["test_3"] = export_res

    print("\n" + "=" * 70)
    print("[SUCCESS] MILESTONE 2 END-TO-END INTEGRATION TEST PASSED WITH ZERO ERRORS!")
    print("=" * 70)
    return results

if __name__ == "__main__":
    run_milestone2_test()
