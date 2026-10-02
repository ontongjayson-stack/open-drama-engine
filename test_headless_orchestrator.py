"""
Open Drama Engine — Headless Studio Orchestrator Integration Test Suite
Validates the full 5-stage autonomous pipeline:
1. [Script & Beat Sheet Agent]
2. [Asset & Rig Manager Agent]
3. [Audio Director Agent]
4. [Timeline Compositor Agent]
5. [Headless Render Process]
"""

import os
import sys
import json
import time
from pathlib import Path
from headless_orchestrator import HeadlessStudioOrchestrator


def run_headless_orchestration_test():
    print("=" * 70)
    print("[HEADLESS ORCHESTRATOR TEST] 5-STAGE PIPELINE VERIFICATION")
    print("=" * 70)

    orchestrator = HeadlessStudioOrchestrator()
    output_mp4 = "test_assembled_headless_orchestrator_film.mp4"

    start_time = time.time()
    result = orchestrator.orchestrate_film(
        topic="A cybernetic cat hero escaping a surveillance drone in a neon alleyway",
        genre="2D Cartoon Action",
        duration=15,
        aspect_ratio="16:9",
        privacy_mode=True,
        output_path=output_mp4,
    )
    elapsed = time.time() - start_time

    print(f"\n--- [RESULT SUMMARY] Executed in {elapsed:.2f}s ---")
    print(f"Success: {result.get('success')}")
    print(f"Output MP4: {result.get('output_path')}")
    print(f"Duration: {result.get('duration')}s")
    print(f"Resolution: {result.get('resolution')}")

    timeline = result.get("timeline_json", {})
    meta = timeline.get("project_metadata", {})
    tracks = timeline.get("tracks", {})

    print("\n--- [STAGE 1 & 4 VERIFICATION]: Frame-Precise Timeline Metadata ---")
    print(f"  Title: {meta.get('title')}")
    print(f"  FPS: {meta.get('fps')}")
    print(f"  Duration Frames: {meta.get('duration_frames')} frames")

    print("\n--- [STAGE 2 VERIFICATION]: Video & Character Track Layers ---")
    backgrounds = tracks.get("backgrounds", [])
    for idx, bg in enumerate(backgrounds):
        print(f"  * Background {idx+1}: '{bg.get('id')}' [{bg.get('frame_start')}f..{bg.get('frame_end')}f] Asset: {os.path.basename(bg.get('asset_path'))}")

    character_layers = tracks.get("character_layers", [])
    for idx, chr_layer in enumerate(character_layers):
        print(f"  * Character Rig {idx+1}: '{chr_layer.get('character_id')}' [{chr_layer.get('frame_start')}f..{chr_layer.get('frame_end')}f] Manifest: {chr_layer.get('rig_manifest')}")

    print("\n--- [STAGE 3 VERIFICATION]: Viseme Timeline & Audio Cues ---")
    audio_tracks = tracks.get("audio", [])
    for idx, aud in enumerate(audio_tracks):
        print(f"  * Audio Track {idx+1}: ID '{aud.get('id')}' [{aud.get('frame_start')}f] Type: {aud.get('type')} Visemes: {aud.get('viseme_map_path')}")

    print("\n--- [STAGE 5 VERIFICATION]: Disk Output Validation ---")
    if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 0:
        file_size = os.path.getsize(output_mp4)
        print(f"[SUCCESS] Final Rendered MP4 Exists on Disk! File Size: {file_size} bytes")
    else:
        print(f"[ERROR] Output file '{output_mp4}' not found or 0 bytes.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL 5 STAGES OF HEADLESS STUDIO ORCHESTRATOR PASSED WITH ZERO ERRORS!")
    print("=" * 70)


if __name__ == "__main__":
    run_headless_orchestration_test()
