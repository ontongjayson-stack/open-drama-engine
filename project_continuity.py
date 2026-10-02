"""Immutable project canon, visual evidence, and actual decoded frame handoffs."""
import base64
import hashlib
import json
import os
from pathlib import Path
import requests
from PIL import Image
from prompt_guard import ContinuityError, PromptGuard
from story_writer import parse_object
from story_media import run_media, probe


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frame(video, destination, last=False):
    stream = next(s for s in probe(video)["streams"] if s["codec_type"] == "video")
    count = int(stream.get("nb_frames", 0))
    if last and count <= 0:
        raise ContinuityError("Cannot verify this clip's final frame.")
    run_media(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", f"select=eq(n\\,{count - 1 if last else 0})", "-frames:v", "1", str(destination)])
    return destination


def pixel_hash(path):
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        return hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()


def verify_master_joins(master, clips, root):
    indices, total = [], 0
    for clip in clips[:-1]:
        stream = next(s for s in probe(clip)["streams"] if s["codec_type"] == "video")
        total += int(stream["nb_frames"])
        indices += [total - 1, total]
    if not indices:
        return
    destination = Path(root) / "master_join_frames"
    destination.mkdir(exist_ok=True)
    expression = "+".join(f"eq(n\\,{n})" for n in indices)
    run_media(["ffmpeg", "-y", "-v", "error", "-i", str(master), "-vf", f"select={expression}", "-fps_mode", "vfr", "-frames:v", str(len(indices)), str(destination / "%05d.png")])
    for i in range(1, len(indices) + 1, 2):
        if pixel_hash(destination / f"{i:05d}.png") != pixel_hash(destination / f"{i+1:05d}.png"):
            raise ContinuityError(f"Final movie frame handoff failed at scene join {(i+1)//2}.")


def creator_export(master, clips, root):
    """Fixed-quantizer intra frames give identical source joins identical coding."""
    root = Path(root)
    lossless = root / "continuity_master.mp4"
    verify_master_joins(master, clips, root)
    Path(master).replace(lossless)
    delivery = root / "delivery.tmp.mp4"
    run_media(["ffmpeg", "-y", "-v", "error", "-i", str(lossless), "-map", "0", "-c:v", "libx264", "-preset", "veryfast", "-qp", "18", "-g", "1", "-keyint_min", "1", "-sc_threshold", "0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-c:s", "copy", "-movflags", "+faststart", str(delivery)])
    # Verify the delivered file, not merely intermediate lossless scene clips.
    verify_master_joins(delivery, clips, root)
    delivery.replace(master)
    return str(master)


class ProjectContinuity:
    def __init__(self, root, story, keys):
        self.root, self.keys, self.guard = Path(root), keys, PromptGuard()
        self.canon = {"version": 1, "title": story["title"], "character_bible": story["character_bible"], "shots": story["shots"]}
        path = self.root / "canon.json"
        if path.exists():
            if json.loads(path.read_text(encoding="utf-8")) != self.canon:
                raise ContinuityError("Saved project canon differs from this screenplay. Create a new project to change the cast or story.")
        else:
            path.write_text(json.dumps(self.canon, indent=2), encoding="utf-8")
        self.digest = file_hash(path)
        reference = self.root / "character_reference.png"
        lock = self.root / "reference.lock.json"
        if reference.exists():
            if not lock.exists() or json.loads(lock.read_text(encoding="utf-8")).get("sha256") != file_hash(reference):
                raise ContinuityError("The saved character reference has changed or is unverified. Create a new project rather than changing identity mid-film.")

    def lock_reference(self, reference):
        (self.root / "reference.lock.json").write_text(json.dumps({"sha256": file_hash(reference)}), encoding="utf-8")

    def observe(self, images, instruction):
        gemini_key, openrouter_key = self.keys.get("gemini"), self.keys.get("openrouter")
        if not (gemini_key or openrouter_key):
            raise ContinuityError("Visual character verification requires an existing vision-capable generation account.")
        text = instruction + " Return EXACTLY JSON {observations: detailed factual text, contradictions: array of strings, uncertain: boolean}. Do not assume identical people from prompts; inspect faces, hair, eyes, clothing and accessories. Unreadable identity details must be marked uncertain."
        encoded = [(label, base64.b64encode(Path(path).read_bytes()).decode("ascii")) for label, path in images]
        failures, evidence = [], None
        if gemini_key:
            parts = [{"text": text}]
            for label, data in encoded:
                parts += [{"text": label}, {"inline_data": {"mime_type": "image/png", "data": data}}]
            model = os.getenv("CONTINUITY_VISION_MODEL", os.getenv("GEMINI_MODEL", "gemini-flash-latest"))
            try:
                response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", headers={"x-goog-api-key": gemini_key}, json={"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0, "maxOutputTokens": 3000}}, timeout=(10, 90))
                if response.ok:
                    evidence = parse_object("".join(p.get("text", "") for p in response.json()["candidates"][0]["content"]["parts"] if not p.get("thought")))
                else:
                    failures.append(f"Gemini HTTP {response.status_code}")
            except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
                failures.append("Gemini returned no valid observations")
        if evidence is None and openrouter_key and os.getenv("ALLOW_OPENROUTER_VISION") == "1":
            content = [{"type": "text", "text": text}]
            for label, data in encoded:
                content += [{"type": "text", "text": label}, {"type": "image_url", "image_url": {"url": "data:image/png;base64," + data}}]
            model = os.getenv("OPENROUTER_VISION_MODEL", "google/gemma-4-26b-a4b-it:free")
            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {openrouter_key}"}, json={"model": model, "messages": [{"role": "user", "content": content}], "response_format": {"type": "json_object"}, "reasoning": {"enabled": False, "exclude": True}, "temperature": 0, "max_tokens": 6000}, timeout=(10, 120))
                if response.ok:
                    evidence = parse_object(response.json()["choices"][0]["message"]["content"])
                else:
                    failures.append(f"OpenRouter HTTP {response.status_code}")
            except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
                failures.append("OpenRouter returned no valid observations")
        if evidence is None and openrouter_key and os.getenv("ALLOW_OPENROUTER_VISION") != "1":
            failures.append("OpenRouter visual fallback awaits explicit approval to send generated images")
        if evidence is None:
            raise ContinuityError("Visual identity observer unavailable: " + "; ".join(failures) + ". No unchecked art was accepted.")
        if not isinstance(evidence.get("observations"), str) or not isinstance(evidence.get("contradictions"), list) or evidence.get("uncertain") is not False or evidence["contradictions"]:
            raise ContinuityError("Visual character identity is contradictory or uncertain. Regenerate the scene before export.")
        return evidence

    def approve_art(self, art, index, reference=None):
        images = [("Candidate scene", art)]
        if reference:
            images.insert(0, ("Immutable project character reference", reference))
        evidence = self.observe(images, "Verify visible characters against this fixed bible: " + self.canon["character_bible"])
        self.guard.approve({"canon": self.canon["character_bible"], "scene": self.canon["shots"][index-1], "visual_evidence": evidence}, {"identity": "Do observations explicitly confirm the same cast identity, face, hair, eyes, costume and defining accessories as the fixed canon/reference?", "scene": "Does the observed scene support the planned scene without contradictory characters or location?"}, self.root / f"identity_{index:04d}.json")
        return file_hash(art)

    def approve_clip(self, clip, index, previous=None):
        first = frame(clip, self.root / f"start_{index:04d}.png")
        last = frame(clip, self.root / f"end_{index:04d}.png", last=True)
        if previous and pixel_hash(previous) != pixel_hash(first):
            raise ContinuityError(f"Scene {index} does not start with the previous scene's exact decoded final frame.")
        record = {"canon_sha256": self.digest, "clip_sha256": file_hash(clip), "start_pixel_sha256": pixel_hash(first), "end_pixel_sha256": pixel_hash(last), "previous_end_pixel_sha256": pixel_hash(previous) if previous else None}
        (self.root / f"handoff_{index:04d}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        return last
