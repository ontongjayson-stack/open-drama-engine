"""One durable story pipeline shared by the dashboard and headless CLI."""
import json
import shutil
from pathlib import Path

from assemble_clips import build_master_story, is_valid_mp4, get_video_duration
from omnirouter import OmniRouter, expand_prompt_with_style
from story_media import captions, dimensions, render_scene, speak, run_media
from prompt_guard import PromptGuard, ContinuityError
from project_continuity import ProjectContinuity, file_hash, creator_export


class StoryProduction:
    def __init__(self, workspace_dir=None):
        self.workspace = Path(workspace_dir) if workspace_dir else Path(__file__).resolve().parent
        self.router = OmniRouter(self.workspace)

    def run(self, job_id, prompt, duration=300, style="Anime", aspect_ratio="16:9", resolution="HD (720p)", character_anchor="", engine_provider="auto", include_subtitles=True, production_mode="story", video_backend="local", custom_video_url="", callback=None, **unused):
        self.router._refresh_keys()
        PromptGuard().require_config()
        if production_mode != "story":
            raise ContinuityError("Motion providers do not yet support verified character references and exact frame handoffs. Use the continuity-checked illustrated story format.")
        self.router._refresh_keys()
        if not (self.router.keys.get("gemini") or self.router.keys.get("openrouter")):
            raise ContinuityError("An existing vision-capable generation account is required before export.")
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise RuntimeError("FFmpeg and FFprobe are required on PATH. Restart the application after installing FFmpeg.")
        root = self.workspace / "generated_assets" / "jobs" / job_id
        root.mkdir(parents=True, exist_ok=True)
        settings = {"prompt": prompt, "duration": duration, "style": style, "aspect_ratio": aspect_ratio, "resolution": resolution, "character_anchor": character_anchor, "include_subtitles": include_subtitles, "production_mode": production_mode}
        settings_file = root / "production_settings.json"
        if settings_file.exists() and json.loads(settings_file.read_text(encoding="utf-8")) != settings:
            raise ContinuityError("Project output settings are fixed. Create a new project to change its format, character, or story.")
        settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
        if production_mode == "story" and not self.router._check_comfyui_online():
            raise RuntimeError(f"Local scene-art engine is offline at {self.router.comfyui_base_url}. Start ComfyUI and retry.")
        def update(percent, stage, message):
            if callback:
                callback({"percent": percent, "active_agent": stage, "status_text": message, "agent_activity": message, "log": message, "log_type": "info"})
        script_file = root / "story.json"
        story = self.router.generate_story(prompt, style, duration, character_anchor, engine_provider, lambda msg: update(12, "writer", msg), cache_dir=root)
        script_file.write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")
        (root / "script.txt").write_text(story["scriptText"], encoding="utf-8")
        continuity = ProjectContinuity(root, story, self.router.keys)
        previous = None
        reference = root / "character_reference.png"
        shots = story["shots"]
        clips, cues = [], []
        offset = 0.0
        for index, shot in enumerate(shots, 1):
            scene_duration = float(shot["duration"])
            clip = root / f"scene_{index:04d}.mp4"
            narration = shot["narration"]
            scene_cues = captions(narration, scene_duration, offset, len(cues) + 1)
            cues.extend(scene_cues)
            offset += scene_duration
            progress = 20 + int((index - 1) / len(shots) * 70)
            voice = root / f"narration_{index:04d}.wav"
            update(progress, "voice", f"Scene {index}/{len(shots)}: Recording narration...")
            if not voice.exists():
                speak(narration, voice)
            subtitle_file = root / f"scene_{index:04d}.srt"
            subtitle_file.write_text("".join(captions(narration, scene_duration)), encoding="utf-8")
            raw = root / f"art_{index:04d}.png"
            update(progress + 1, "artist", f"Scene {index}/{len(shots)}: Rendering and checking fixed character identity...")
            receipt = root / f"art_receipt_{index:04d}.json"
            trusted = False
            if raw.exists() and receipt.exists():
                saved = json.loads(receipt.read_text(encoding="utf-8"))
                trusted = saved.get("art_sha256") == file_hash(raw) and saved.get("canon_sha256") == continuity.digest and saved.get("reference_sha256") == (file_hash(reference) if reference.exists() else None)
            if not trusted:
                accepted = False
                for attempt in range(3):
                    description = story["character_bible"] + ". " + shot["prompt"]
                    positive, negative = expand_prompt_with_style(description, style)
                    self.router.generate_image(positive, negative, aspect_ratio, output_path=raw, reference=previous or (reference if reference.exists() else None))
                    try:
                        continuity.approve_art(raw, index, reference if reference.exists() else None)
                    except ContinuityError as exc:
                        update(progress + 1, "reviewer", f"Scene {index}: {exc}")
                        if attempt == 2:
                            raise
                        continue
                    accepted = True
                    break
                if not accepted:
                    raise ContinuityError("Visual identity could not be verified.")
                if not reference.exists():
                    shutil.copy2(raw, reference)
                    continuity.lock_reference(reference)
                receipt.write_text(json.dumps({"art_sha256": file_hash(raw), "canon_sha256": continuity.digest, "reference_sha256": file_hash(reference)}), encoding="utf-8")
            handoff = root / f"handoff_{index:04d}.json"
            reusable = False
            if clip.exists() and handoff.exists() and is_valid_mp4(clip):
                saved = json.loads(handoff.read_text(encoding="utf-8"))
                reusable = saved.get("art_sha256") == file_hash(raw) and saved.get("clip_sha256") == file_hash(clip) and saved.get("canon_sha256") == continuity.digest and abs(get_video_duration(clip)-scene_duration) < .2
            if not reusable:
                update(progress + 2, "director", f"Scene {index}/{len(shots)}: Rendering with a lossless frame handoff...")
                render_scene(raw, voice, scene_duration, clip, aspect_ratio, resolution, strict_continuity=True, continuity_start=previous)
            previous = continuity.approve_clip(clip, index, previous)
            saved = json.loads(handoff.read_text(encoding="utf-8"))
            saved["art_sha256"] = file_hash(raw)
            handoff.write_text(json.dumps(saved, indent=2), encoding="utf-8")
            clips.append(clip)
        (root / "subtitles.srt").write_text("".join(cues), encoding="utf-8")
        update(94, "composer", "Assembling and verifying the complete story...")
        output = build_master_story(root, clips=clips, expected_duration=duration)
        if include_subtitles:
            subtitled = root / "subtitled.tmp.mp4"
            run_media(["ffmpeg", "-y", "-v", "error", "-i", output, "-i", str(root / "subtitles.srt"), "-map", "0", "-map", "1:0", "-c", "copy", "-c:s", "mov_text", "-disposition:s:0", "default", "-movflags", "+faststart", str(subtitled)])
            subtitled.replace(output)
        output = creator_export(output, clips, root)
        width, height = dimensions(aspect_ratio, resolution)
        result = {"success": True, "job_id": job_id, "output_path": output, "title": story["title"], "duration": get_video_duration(output), "resolution": f"{width}x{height}", "scene_count": len(shots), "mode": production_mode, "continuity": "verified_frame_handoffs_and_model_reviewed_identity", "script_path": str(script_file), "subtitles_path": str(root / "subtitles.srt")}
        (root / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
