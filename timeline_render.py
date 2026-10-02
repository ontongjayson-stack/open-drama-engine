"""Render supported background/audio timeline tracks; reject unsupported rigs."""
import tempfile
from pathlib import Path

from assemble_clips import build_master_story
from story_media import render_scene


def render_timeline(timeline, output_path, workspace=None):
    workspace = Path(workspace) if workspace else Path(__file__).resolve().parent
    timeline = timeline.get("timeline", timeline.get("data", timeline))
    metadata, tracks = timeline["project_metadata"], timeline["tracks"]
    if tracks.get("character_layers") or tracks.get("props"):
        raise ValueError("Rig and prop animation is not implemented. Export a background/art and narration timeline instead.")
    backgrounds = sorted(tracks.get("backgrounds", []), key=lambda b: b["frame_start"])
    if not backgrounds:
        raise ValueError("Timeline has no renderable backgrounds.")
    fps = float(metadata["fps"])
    size = metadata["resolution"]
    ratio = "16:9" if size["width"] > size["height"] else "9:16" if size["height"] > size["width"] else "1:1"
    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    def resolve(path):
        value = Path(path)
        return value if value.is_absolute() else workspace / value
    position, clips = 0, []
    with tempfile.TemporaryDirectory(prefix="timeline_", dir=target.parent) as scratch:
        scratch = Path(scratch)
        for index, bg in enumerate(backgrounds):
            if bg["frame_start"] != position or bg["frame_end"] <= position:
                raise ValueError("Background tracks must form one contiguous, non-overlapping timeline.")
            audio = [a for a in tracks.get("audio", []) if a["frame_start"] == position]
            if len(audio) > 1:
                raise ValueError("Only one narration track per scene is supported.")
            clip = scratch / f"scene_{index:04d}.mp4"
            render_scene(resolve(bg["asset_path"]), resolve(audio[0]["file_path"]) if audio else None, (bg["frame_end"] - position) / fps, clip, ratio, "HD (720p)", fps=int(fps))
            position = bg["frame_end"]
            clips.append(clip)
        if position != metadata["duration_frames"]:
            raise ValueError("Timeline backgrounds do not cover the declared duration.")
        output = build_master_story(scratch, clips=clips, expected_duration=position / fps)
        import shutil
        shutil.copyfile(output, target)
    return {"success": True, "output_path": str(target), "duration": position / fps}
