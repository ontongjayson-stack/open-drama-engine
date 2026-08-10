"""
Open Drama Engine — Production Render Engine (render_engine.py)
Powered by MoviePy, Librosa, PIL, and NumPy.
Performs audio beat detection, frame-by-frame Ken Burns camera movements (zoom/pan),
cinematic visual overlays (vignette, film grain, letterboxing, text metadata), and MP4 sequence export.
"""

import os
import sys
import time
import math
import logging
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

import librosa
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, VideoClip

logging.basicConfig(level=logging.INFO, format="[RenderEngine] %(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RenderEngine")


class RenderEngine:
    """
    Cinematic Video Assembly & Compositing Engine
    """

    def __init__(self, fps=24, default_resolution=(1280, 720)):
        self.fps = fps
        self.default_resolution = default_resolution

    # -------------------------------------------------------------------------
    # 1. Beat Detection with Librosa
    # -------------------------------------------------------------------------
    def detect_beats(self, audio_path, target_duration=None, min_interval=1.5):
        """
        Analyzes audio file using Librosa to detect onset beat timestamps in seconds.
        Falls back gracefully to fixed interval pulses if audio loading fails or is absent.
        """
        if not audio_path or not os.path.exists(audio_path):
            logger.warning(f"Audio file '{audio_path}' not found. Using fallback 2.5s beat grid.")
            return self._generate_fallback_beats(target_duration or 15.0, min_interval)

        try:
            logger.info(f"Performing Librosa Beat Detection on '{audio_path}'...")
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)

            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

            logger.info(f"Detected estimated tempo: {float(tempo):.1f} BPM across {duration:.2f}s audio.")

            filtered_beats = [0.0]
            for t in beat_times:
                if t - filtered_beats[-1] >= min_interval:
                    filtered_beats.append(round(t, 2))

            if duration not in filtered_beats and duration > filtered_beats[-1]:
                filtered_beats.append(round(duration, 2))

            logger.info(f"Beat timestamps selected for cuts ({len(filtered_beats)} scene markers): {filtered_beats}")
            return filtered_beats

        except Exception as err:
            logger.warning(f"Librosa beat analysis error: {err}. Falling back to default beat interval.")
            return self._generate_fallback_beats(target_duration or 15.0, min_interval)

    def _generate_fallback_beats(self, total_duration, interval=2.5):
        timestamps = []
        t = 0.0
        while t < total_duration:
            timestamps.append(round(t, 2))
            t += interval
        timestamps.append(round(total_duration, 2))
        return timestamps

    # -------------------------------------------------------------------------
    # 2. Cinematic Visual Overlays (Vignette, Film Grain, Letterbox, Text)
    # -------------------------------------------------------------------------
    def apply_cinematic_overlays(
        self,
        pil_img,
        title_text="",
        subtitle_text="",
        add_vignette=True,
        add_film_grain=True,
        add_letterbox=True,
        letterbox_ratio=0.10,
    ):
        """
        Applies aesthetic cinematic filters: radial vignette, film grain texture,
        widescreen letterboxing, and stylized text metadata.
        """
        img = pil_img.convert("RGB")
        w, h = img.size

        # 1. Vignette Filter
        if add_vignette:
            vignette_mask = self._create_vignette_mask(w, h)
            img = Image.composite(img, Image.new("RGB", (w, h), (0, 0, 0)), vignette_mask)

        # 2. Film Grain Overlay
        if add_film_grain:
            img = self._apply_film_grain(img, intensity=0.04)

        # 3. Letterbox Black Bars
        draw = ImageDraw.Draw(img)
        if add_letterbox:
            bar_height = int(h * letterbox_ratio)
            draw.rectangle([0, 0, w, bar_height], fill=(0, 0, 0))
            draw.rectangle([0, h - bar_height, w, h], fill=(0, 0, 0))

        # 4. Text & Metadata Overlay
        if title_text or subtitle_text:
            try:
                font_title = ImageFont.truetype("arial.ttf", int(h * 0.04))
                font_sub = ImageFont.truetype("arial.ttf", int(h * 0.025))
            except IOError:
                font_title = ImageFont.load_default()
                font_sub = ImageFont.load_default()

            if title_text:
                draw.text((int(w * 0.05), int(h * 0.82)), title_text, fill=(255, 255, 255), font=font_title)
            if subtitle_text:
                draw.text((int(w * 0.05), int(h * 0.88)), subtitle_text, fill=(200, 210, 230), font=font_sub)

        return img

    def _create_vignette_mask(self, w, h):
        """Generates a radial gradient mask for vignette darkening."""
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        xx, yy = np.meshgrid(x, y)
        radius = np.sqrt(xx**2 + yy**2)
        vignette = np.clip(1.0 - (radius / 1.4) ** 2, 0.2, 1.0)
        mask_array = (vignette * 255).astype(np.uint8)
        return Image.fromarray(mask_array).convert("L")

    def _apply_film_grain(self, pil_img, intensity=0.04):
        """Adds subtle gaussian film grain noise to PIL image."""
        arr = np.array(pil_img, dtype=np.float32)
        noise = np.random.normal(0, intensity * 255, arr.shape)
        noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_arr).convert("RGB")

    # -------------------------------------------------------------------------
    # 3. Ken Burns Frame-by-Frame Motion Generator
    # -------------------------------------------------------------------------
    def create_ken_burns_clip(
        self, image_input, duration, mode="zoom_in", resolution=(1280, 720), overlays_config=None
    ):
        """
        Creates a Ken Burns MoviePy VideoClip with continuous frame-by-frame zoom and pan movement.
        Modes: 'zoom_in', 'zoom_out', 'pan_right', 'pan_left'
        """
        w_target, h_target = resolution

        if isinstance(image_input, (str, Path)):
            base_pil = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            base_pil = image_input.convert("RGB")
        else:
            raise ValueError("image_input must be a file path or PIL Image instance.")

        if overlays_config:
            base_pil = self.apply_cinematic_overlays(base_pil, **overlays_config)

        orig_w, orig_h = base_pil.size

        start_scale = 1.0
        end_scale = 1.15
        if mode == "zoom_out":
            start_scale, end_scale = 1.15, 1.0

        def make_frame(t):
            progress = min(1.0, max(0.0, t / duration if duration > 0 else 0))
            current_scale = start_scale + (end_scale - start_scale) * progress

            crop_w = int(orig_w / current_scale)
            crop_h = int(orig_h / current_scale)

            if mode == "pan_right":
                pan_x = int((orig_w - crop_w) * progress)
                pan_y = int((orig_h - crop_h) / 2)
            elif mode == "pan_left":
                pan_x = int((orig_w - crop_w) * (1.0 - progress))
                pan_y = int((orig_h - crop_h) / 2)
            else:  # Center zoom
                pan_x = int((orig_w - crop_w) / 2)
                pan_y = int((orig_h - crop_h) / 2)

            crop_box = (
                max(0, pan_x),
                max(0, pan_y),
                min(orig_w, pan_x + crop_w),
                min(orig_h, pan_y + crop_h),
            )
            cropped = base_pil.crop(crop_box)
            resized = cropped.resize((w_target, h_target), Image.Resampling.LANCZOS)
            return np.array(resized)

        clip = VideoClip(frame_function=make_frame, duration=duration)
        return clip

    # -------------------------------------------------------------------------
    # 4. Multi-Shot Sequence Assembly & Export to MP4
    # -------------------------------------------------------------------------
    def render_sequence(
        self,
        shots,
        audio_path=None,
        output_path="output_render.mp4",
        aspect_ratio="16:9",
        bpm_sync=True,
    ):
        """
        Assembles multiple keyframe shots into a finished video sequence,
        snaps scene cuts to audio beat timestamps, applies Ken Burns & FX, and exports to MP4.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        w_target, h_target = self._parse_aspect_ratio(aspect_ratio)
        res = (w_target, h_target)

        total_shots = len(shots)
        if total_shots == 0:
            raise ValueError("No shots provided for render_sequence.")

        logger.info(f"Starting Sequence Render for {total_shots} shot(s) (Target: {w_target}x{h_target} @ {self.fps}fps)...")

        total_duration = sum(s.get("duration", 4.0) for s in shots)
        beat_markers = self.detect_beats(audio_path, target_duration=total_duration) if bpm_sync else []

        durations = []
        if len(beat_markers) >= total_shots + 1:
            for i in range(total_shots):
                dur = beat_markers[i + 1] - beat_markers[i]
                durations.append(max(1.0, round(dur, 2)))
        else:
            durations = [shot.get("duration", 4.0) for shot in shots]

        motion_modes = ["zoom_in", "pan_right", "zoom_out", "pan_left"]

        video_clips = []
        for idx, shot in enumerate(shots):
            img_path = shot.get("image_path") or shot.get("url")
            shot_title = shot.get("title") or f"SHOT {idx+1:02d}"
            shot_prompt = shot.get("prompt", "")
            duration = durations[idx] if idx < len(durations) else 4.0
            motion_mode = motion_modes[idx % len(motion_modes)]

            logger.info(f"Rendering Shot {idx+1}/{total_shots}: '{shot_title}' ({duration:.2f}s, Motion: {motion_mode})...")

            overlays_config = {
                "title_text": shot_title,
                "subtitle_text": shot_prompt[:60] + "..." if len(shot_prompt) > 60 else shot_prompt,
                "add_vignette": True,
                "add_film_grain": True,
                "add_letterbox": True,
            }

            clip = self.create_ken_burns_clip(
                image_input=img_path,
                duration=duration,
                mode=motion_mode,
                resolution=res,
                overlays_config=overlays_config,
            )
            video_clips.append(clip)

        final_video = concatenate_videoclips(video_clips, method="compose")

        if audio_path and os.path.exists(audio_path):
            try:
                logger.info(f"Attaching Audio Track from '{audio_path}'...")
                audio_clip = AudioFileClip(audio_path)
                if audio_clip.duration > final_video.duration:
                    audio_clip = audio_clip.subclipped(0, final_video.duration)
                final_video = final_video.with_audio(audio_clip)
            except Exception as err:
                logger.warning(f"Failed to attach audio track: {err}")

        logger.info(f"Writing MP4 Video File to '{output_path}'...")
        final_video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        logger.info(f"Render Complete! Output saved to: {output_path}")
        return {
            "success": True,
            "output_path": str(output_path),
            "duration": final_video.duration,
            "resolution": f"{w_target}x{h_target}",
        }

    def _parse_aspect_ratio(self, ratio_str):
        if ratio_str == "9:16":
            return (720, 1280)
        elif ratio_str == "1:1":
            return (1080, 1080)
        return (1280, 720)


if __name__ == "__main__":
    from omnirouter import OmniRouter

    print("Executing RenderEngine Standalone Test...")
    router = OmniRouter()

    shot1 = router.generate_image("A futuristic cyberpunk city skyline with flying cars", aspect_ratio="16:9")
    shot2 = router.generate_image("A dramatic anime character looking at the neon rain", aspect_ratio="16:9")

    shot1["title"] = "SHOT 01: CYBER CITY"
    shot2["title"] = "SHOT 02: NEON RAIN"

    engine = RenderEngine(fps=24)
    out = engine.render_sequence(
        shots=[shot1, shot2],
        output_path="test_sequence_render.mp4",
        aspect_ratio="16:9",
        bpm_sync=False,
    )
    print("Render Output:", out)
