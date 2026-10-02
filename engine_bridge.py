"""
Open Drama Engine — Bridge CLI Controller (engine_bridge.py)
Connects server.js and Electron backend to omnirouter.py and render_engine.py.
Handles CLI parameters and JSON payloads for image generation, script generation,
multi-provider routing, and beat-synced Ken Burns MP4 sequence rendering.
"""

import sys
import json
import argparse
from pathlib import Path
from omnirouter import OmniRouter
from render_engine import RenderEngine
from headless_orchestrator import HeadlessStudioOrchestrator


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Open Drama Engine Bridge")
    parser.add_argument("--action", choices=["status", "generate_shot", "generate_script", "refine_shot", "render_sequence", "render_timeline", "orchestrate"], required=True)
    parser.add_argument("--payload", type=str, help="JSON payload string or file path")
    parser.add_argument("--out", type=str, help="Output MP4 or image file path")

    args = parser.parse_args()
    router = OmniRouter()

    if args.action == "status":
        status = router.get_provider_status()
        print(json.dumps(status))
        return

    # Parse Payload
    payload = {}
    if args.payload:
        try:
            if args.payload.lstrip().startswith(("{", "[")):
                payload = json.loads(args.payload)
            elif Path(args.payload).exists():
                with open(args.payload, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            else:
                payload = json.loads(args.payload)
        except Exception as err:
            print(json.dumps({"error": f"Failed to parse payload: {err}"}))
            sys.exit(1)

    if args.action in ("generate_shot", "render_sequence", "render_timeline"):
        print(json.dumps({"error": "Independent shot/timeline generation cannot enforce project continuity. Use orchestrate, which verifies canon, visual identity, and every frame handoff."}))
        sys.exit(1)

    if args.action == "render_timeline":
        from timeline_render import render_timeline
        print(json.dumps(render_timeline(payload, args.out or "timeline_output.mp4")))

    elif args.action == "orchestrate":
        topic = payload.get("topic", "Cybernetic Cat Hero Escaping Surveillance Drone in Neon Alley")
        genre = payload.get("genre", "2D Cartoon Action")
        duration = payload.get("duration", 300)
        aspect_ratio = payload.get("aspectRatio", "16:9")
        privacy_mode = payload.get("privacyMode", False)
        output_path = args.out or payload.get("outputPath") or "headless_sequence_output.mp4"

        orchestrator = HeadlessStudioOrchestrator()
        result = orchestrator.orchestrate_film(
            topic=topic,
            genre=genre,
            duration=duration,
            aspect_ratio=aspect_ratio,
            privacy_mode=privacy_mode,
            output_path=output_path,
            character_anchor=payload.get("characterAnchor", ""),
            provider=payload.get("provider", "auto"),
        )
        print(json.dumps(result))

    elif args.action == "generate_script":
        topic = payload.get("topic", "Cybernetic cat hero action scene")
        genre = payload.get("genre", "2D Cartoon Action")
        target_duration = payload.get("targetDuration", 30)

        result = router.generate_script(
            topic=topic,
            genre=genre,
            target_duration=target_duration,
        )
        print(json.dumps(result))

    elif args.action == "refine_shot":
        shot_id = payload.get("shotId", 1)
        original_prompt = payload.get("originalPrompt", "")
        tweak_instruction = payload.get("tweakInstruction", "")
        topic = payload.get("topic", "General")
        genre = payload.get("genre", "2D Cartoon Action")

        result = router.refine_shot(
            shot_id=shot_id,
            original_prompt=original_prompt,
            tweak_instruction=tweak_instruction,
            topic=topic,
            genre=genre
        )
        print(json.dumps(result))

    elif args.action == "generate_shot":
        prompt = payload.get("prompt", "2D animated scene")
        negative_prompt = payload.get("negativePrompt", "")
        aspect_ratio = payload.get("aspectRatio", "16:9")
        preferred_provider = payload.get("provider")
        privacy_mode = payload.get("privacyMode", False)

        result = router.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            preferred_provider=preferred_provider,
            privacy_mode=privacy_mode,
        )

        # Build Ken Burns video preview from generated image frame
        if result.get("success"):
            engine = RenderEngine(fps=24)
            preview_mp4 = Path(result["image_path"]).with_suffix(".mp4")
            try:
                clip_out = engine.render_sequence(
                    shots=[{
                        "image_path": result["image_path"],
                        "title": f"SHOT: {prompt[:30]}",
                        "prompt": prompt,
                        "duration": 5.0,
                    }],
                    output_path=str(preview_mp4),
                    aspect_ratio=aspect_ratio,
                    bpm_sync=False,
                )
                result["video_path"] = str(preview_mp4)
            except Exception as err:
                pass

        print(json.dumps(result))

    elif args.action == "render_sequence":
        shots = payload.get("shots", [])
        audio_path = payload.get("audioPath")
        aspect_ratio = payload.get("aspectRatio", "16:9")
        privacy_mode = payload.get("privacyMode", False)
        output_path = args.out or payload.get("outputPath") or "output_sequence.mp4"

        processed_shots = []
        for idx, s in enumerate(shots):
            if isinstance(s, str):
                s = {"prompt": s}
            if not s.get("image_path") and not s.get("url"):
                img_res = router.generate_image(
                    prompt=s.get("prompt", f"Scene Shot {idx+1}"),
                    aspect_ratio=aspect_ratio,
                    privacy_mode=privacy_mode,
                )
                s["image_path"] = img_res["image_path"]
            if not s.get("title"):
                s["title"] = f"SHOT {idx+1:02d}"
            processed_shots.append(s)

        engine = RenderEngine(fps=24)
        result = engine.render_sequence(
            shots=processed_shots,
            audio_path=audio_path,
            output_path=output_path,
            aspect_ratio=aspect_ratio,
            bpm_sync=True,
        )
        print(json.dumps(result))


if __name__ == "__main__":
    main()
