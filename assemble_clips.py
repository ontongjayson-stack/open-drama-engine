import os
import subprocess
import tempfile
from pathlib import Path

from story_media import probe, run_media


def is_valid_mp4(file_path):
    try:
        return any(s.get("codec_type") == "video" for s in probe(file_path)["streams"])
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        return False


def get_video_duration(file_path):
    return float(probe(file_path)["format"]["duration"])


def find_audio_track(project_dir):
    for extension in ("mp3", "wav", "m4a", "aac", "flac"):
        files = sorted(Path(project_dir).glob(f"*.{extension}"))
        if files:
            return str(files[0])
    return None


def build_master_story(project_dir, prompts_dict=None, include_subtitles=False, clips=None, expected_duration=None, audio_path=None):
    """Assemble a complete, explicitly ordered story or fail with FFmpeg's error."""
    root = Path(project_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Story directory does not exist: {root}")
    clips = [Path(c).resolve() for c in (clips if clips is not None else sorted(root.glob("scene_*.mp4")))]
    if not clips:
        raise ValueError("No scene clips were provided for assembly.")
    for clip in clips:
        if not is_valid_mp4(clip):
            raise RuntimeError(f"Scene is missing or invalid: {clip}")
    metadata = [probe(c) for c in clips]
    def signature(info):
        return [(s.get("codec_type"), s.get("codec_name"), s.get("width"), s.get("height"), s.get("r_frame_rate"), s.get("sample_rate"), s.get("channels")) for s in info["streams"]]
    if any(signature(info) != signature(metadata[0]) for info in metadata[1:]):
        raise RuntimeError("Scene formats differ. Normalize resolution, frame rate, and audio before assembling.")
    total = sum(float(info["format"]["duration"]) for info in metadata)
    expected = float(expected_duration) if expected_duration is not None else total
    final = root / "master_story.mp4"
    with tempfile.TemporaryDirectory(prefix="assemble_", dir=root) as scratch:
        scratch = Path(scratch)
        # Numeric relative paths avoid concat quoting problems in Windows paths.
        for index, clip in enumerate(clips):
            destination = scratch / f"clip_{index:05d}.mp4"
            try:
                os.link(clip, destination)
            except OSError:
                import shutil
                shutil.copyfile(clip, destination)
        (scratch / "clips.txt").write_text("".join(f"file 'clip_{i:05d}.mp4'\n" for i in range(len(clips))), encoding="utf-8")
        output = scratch / "master_story.mp4"
        args = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "clips.txt"]
        if audio_path:
            args += ["-stream_loop", "-1", "-i", str(Path(audio_path).resolve()), "-filter_complex", "[1:a]volume=0.18[bg];[0:a][bg]amix=inputs=2:duration=first[a]", "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac"]
        else:
            args += ["-c", "copy"]
        args += ["-t", str(expected), "-movflags", "+faststart", str(output)]
        run_media(args, cwd=scratch, timeout=max(180, int(expected * 3)))
        actual = get_video_duration(output)
        if not is_valid_mp4(output) or abs(actual - expected) > max(0.25, len(clips) / 24):
            raise RuntimeError(f"Master duration verification failed: requested {expected:.3f}s, got {actual:.3f}s.")
        os.replace(output, final)
    return str(final)


if __name__ == "__main__":
    import sys
    print(build_master_story(sys.argv[1] if len(sys.argv) > 1 else "generated_assets"))
