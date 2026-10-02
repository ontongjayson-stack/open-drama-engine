"""Bounded FFmpeg rendering and offline Windows narration for creator exports."""
import json
import math
import os
import shutil
import subprocess
from pathlib import Path


def run_media(args, cwd=None, timeout=1800):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Media processing failed: {result.stderr[-3000:]}")
    return result


def probe(path):
    result = run_media(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(Path(path).resolve())], timeout=30)
    return json.loads(result.stdout)


def dimensions(aspect_ratio="16:9", quality="Standard (512p)"):
    hd = quality == "HD (720p)"
    return {"16:9": (1280, 720) if hd else (768, 432), "9:16": (720, 1280) if hd else (432, 768), "1:1": (720, 720) if hd else (512, 512)}[aspect_ratio]


def speak(text, destination, voice="", rate=0):
    """SAPI is installed with Windows; never substitute silence for failed narration."""
    if os.name != "nt":
        raise RuntimeError("Offline narration currently requires Windows SAPI. Supply a narration WAV on other platforms.")
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    config = destination.with_suffix(".speech.json")
    config.write_text(json.dumps({"text": text, "output": str(destination), "voice": voice, "rate": rate}), encoding="utf-8")
    script = """
$ErrorActionPreference = 'Stop'
$cfg = Get-Content -LiteralPath $env:ODE_SPEECH_CONFIG -Raw -Encoding UTF8 | ConvertFrom-Json
$speaker = New-Object -ComObject SAPI.SpVoice
$stream = New-Object -ComObject SAPI.SpFileStream
try {
  if ($cfg.voice) {
    $match = @($speaker.GetVoices() | Where-Object { $_.GetDescription() -eq $cfg.voice })
    if ($match.Count -eq 0) { throw 'The selected narration voice is not installed.' }
    $speaker.Voice = $match[0]
  }
  $speaker.Rate = [int]$cfg.rate
  $stream.Open($cfg.output, 3, $false)
  $speaker.AudioOutputStream = $stream
  [void]$speaker.Speak($cfg.text, 0)
} finally { $stream.Close() }
"""
    env = dict(os.environ, ODE_SPEECH_CONFIG=str(config))
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], env=env, capture_output=True, text=True, timeout=120)
        if result.returncode or not destination.exists():
            raise RuntimeError(f"Narration failed: {result.stderr[-1500:]}")
        if not any(s["codec_type"] == "audio" for s in probe(destination)["streams"]):
            raise RuntimeError("Narration produced no audio stream.")
    finally:
        config.unlink(missing_ok=True)
    return str(destination)


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def captions(text, duration, offset=0, first_index=1):
    words = text.split()
    groups = [words[i:i + 12] for i in range(0, len(words), 12)]
    cues = []
    position = 0
    for index, group in enumerate(groups, first_index):
        start = offset + duration * position / len(words)
        position += len(group)
        end = offset + duration * position / len(words)
        midpoint = min(6, len(group))
        line = " ".join(group[:midpoint]) + ("\n" + " ".join(group[midpoint:]) if len(group) > midpoint else "")
        cues.append(f"{index}\n{timestamp(start)} --> {timestamp(end)}\n{line}\n\n")
    return cues


def render_scene(source, audio, duration, output, aspect_ratio="16:9", quality="Standard (512p)", fps=24, subtitles=None, is_video=False, motion="zoom_in", continuity_start=None, strict_continuity=False):
    width, height = dimensions(aspect_ratio, quality)
    source, output = Path(source).resolve(), Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    duration = round(float(duration), 3)
    if duration <= 0:
        raise ValueError("Scene duration must be positive.")
    if strict_continuity and (is_video or subtitles):
        raise ValueError("Strict joins require illustrated scenes and separate subtitle tracks.")
    args = ["ffmpeg", "-y", "-v", "error"]
    args += (["-stream_loop", "-1"] if is_video else ["-loop", "1", "-framerate", str(fps)]) + ["-i", str(source)]
    if audio:
        args += ["-i", str(Path(audio).resolve())]
        speech_duration = float(probe(audio)["format"]["duration"])
        speed = max(1.0, speech_duration / max(0.1, duration - 0.2))
        if speed > 1.5:
            raise RuntimeError(f"Narration is too long for this scene ({speech_duration:.1f}s into {duration:.1f}s). Shorten its narration.")
        audio_filter = f"atempo={speed:.6f},apad,atrim=duration={duration},asetpts=PTS-STARTPTS"
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        audio_filter = f"atrim=duration={duration},asetpts=PTS-STARTPTS"
    if continuity_start:
        args += ["-loop", "1", "-framerate", str(fps), "-i", str(Path(continuity_start).resolve())]
    fit = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1"
    if is_video:
        video_filter = f"{fit},fps={fps},trim=duration={duration},setpts=PTS-STARTPTS"
    else:
        frames = math.ceil(duration * fps)
        zoom = f"1.08-0.08*on/{frames}" if motion == "zoom_out" else f"1+0.08*on/{frames}"
        x = "(iw-iw/zoom)*on/" + str(frames) if motion == "pan_right" else "iw/2-(iw/zoom/2)"
        video_filter = f"{fit},zoompan=z='{zoom}':x='{x}':y='ih/2-(ih/zoom/2)':d=1:s={width}x{height}:fps={fps}"
    if subtitles:
        # Work inside the scene directory so FFmpeg filters never parse Windows drive paths.
        subtitle_copy = output.parent / f"{output.stem}.srt"
        if Path(subtitles).resolve() != subtitle_copy:
            shutil.copyfile(subtitles, subtitle_copy)
        video_filter += f",subtitles=filename={subtitle_copy.name}:force_style='FontSize=18,Outline=2,MarginV=24'"
    graph = f"[0:v]{video_filter}[v];[1:a]{audio_filter}[a]"
    if strict_continuity:
        # Lossless RGB prevents independently encoded joins from altering handed-off pixels.
        graph = f"[0:v]{fit},format=gbrp[current];[1:a]{audio_filter}[a]"
        if continuity_start:
            graph += f";[2:v]format=gbrp[previous];[previous][current]blend=all_expr='A*(1-min((N-1)/{fps},1))+B*min((N-1)/{fps},1)',format=rgb24[v]"
        else:
            graph += ";[current]format=rgb24[v]"
    args += ["-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", str(duration), "-r", str(fps), "-c:v", "libx264rgb" if strict_continuity else "libx264", "-preset", "veryfast", "-crf", "0" if strict_continuity else "20", "-pix_fmt", "rgb24" if strict_continuity else "yuv420p", "-c:a", "alac" if strict_continuity else "aac", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(output)]
    run_media(args, cwd=output.parent, timeout=max(180, int(duration * 30)))
    metadata = probe(output)
    if abs(float(metadata["format"]["duration"]) - duration) > 0.2:
        raise RuntimeError("Scene duration verification failed.")
    return str(output)
