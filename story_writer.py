"""Write long stories in bounded batches while carrying the same cast and ending."""
import json
import math
import os
from pathlib import Path

import requests
from prompt_guard import PromptGuard, ContinuityError


def parse_object(text):
    text = str(text).strip()
    if "</think>" in text:
        text = text.split("</think>")[-1]
    start = text.find("{")
    if start < 0:
        raise ValueError("Writer returned no JSON content.")
    value, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(value, dict):
        raise ValueError("Writer returned an invalid JSON object.")
    return value


class StoryWriter:
    def __init__(self, keys, provider="auto"):
        self.guard = PromptGuard()
        self.keys = keys
        self.providers = [provider] if provider != "auto" else ["openrouter", "gemini"]
        if "openrouter" in self.providers:
            self.providers.insert(self.providers.index("openrouter"), "openrouter")

    def request(self, instruction, max_tokens=5000):
        failures = []
        openrouter_attempt = 0
        for provider in self.providers:
            key = self.keys.get(provider)
            if not key:
                failures.append(f"{provider}: API key missing")
                continue
            try:
                if provider == "openrouter":
                    configured_model = os.getenv("OPENROUTER_MODEL")
                    model = configured_model or ("dots-studio/dots-3-note-preview:free" if openrouter_attempt == 0 else "google/gemma-4-26b-a4b-it:free")
                    openrouter_attempt += 1
                    reasoning = {"effort": "minimal", "exclude": True} if configured_model else {"enabled": False, "exclude": True}
                    result = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": model, "messages": [{"role": "system", "content": "You are a professional anime screenplay writer. Return only the requested JSON. All story events must form one coherent beginning, middle and resolved ending."}, {"role": "user", "content": instruction}], "temperature": 0.65, "max_tokens": max(max_tokens, 6000 if openrouter_attempt == 1 else 10000), "response_format": {"type": "json_object"}, "reasoning": reasoning}, timeout=(10, 120))
                    result.raise_for_status()
                    choice = result.json()["choices"][0]
                    text = choice["message"]["content"]
                    if not text or choice.get("finish_reason") == "length":
                        raise ValueError(f"{model} returned no complete screenplay (finish_reason={choice.get('finish_reason')}).")
                elif provider == "gemini":
                    model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
                    result = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", headers={"x-goog-api-key": key}, json={"contents": [{"parts": [{"text": instruction + "\nReturn only JSON."}]}], "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": max_tokens, "temperature": 0.65}}, timeout=(10, 120))
                    result.raise_for_status()
                    text = "".join(p.get("text", "") for p in result.json()["candidates"][0]["content"]["parts"] if not p.get("thought"))
                else:
                    raise ValueError(f"Unsupported writer provider: {provider}")
                return parse_object(text)
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
                # Report the status, never a request URL containing a credential.
                failures.append(f"{provider}: {str(exc) if isinstance(exc, ValueError) else type(exc).__name__}" + (f" HTTP {exc.response.status_code}" if isinstance(exc, requests.HTTPError) else ""))
        raise RuntimeError("Story writing failed (" + "; ".join(failures) + "). Check API keys, provider quota, model settings, and internet access. No placeholder story was exported.")

    def write(self, topic, style, duration, character_anchor="", callback=None, cache_dir=None):
        self.guard.require_config()
        duration = float(duration)
        count = max(1, math.ceil(duration / 12))
        scene_duration = duration / count
        total_frames = round(duration * 24)
        scene_durations = [(total_frames // count + (index < total_frames % count)) / 24 for index in range(count)]
        if callback:
            callback("Writer: Planning the cast, story arc, and final resolution...")
        cache = Path(cache_dir) if cache_dir else None
        if cache:
            cache.mkdir(parents=True, exist_ok=True)
            identity = {"topic": topic, "style": style, "duration": duration, "character_anchor": character_anchor, "continuity_version": 1}
            saved_request = cache / "writer_request.json"
            if saved_request.exists() and json.loads(saved_request.read_text(encoding="utf-8")) != identity:
                raise ContinuityError("This project's writer settings are immutable. Create a new project to change the story or character.")
            saved_request.write_text(json.dumps(identity, indent=2), encoding="utf-8")
        plan = json.loads((cache / "outline.json").read_text(encoding="utf-8")) if cache and (cache / "outline.json").exists() else None
        if plan is None:
            for attempt in range(2):
                candidate = self.request(f"Create an original {duration:.0f}-second narrated anime story about: {topic}. Visual style: {style}. Fixed protagonist description: {character_anchor or 'Invent a distinctive protagonist.'} Return EXACTLY these three top-level keys: {{\"title\":\"...\",\"character_bible\":\"fixed names and precise visual descriptions for the cast\",\"acts\":[\"opening\",\"inciting incident\",\"rising stakes\",\"setback\",\"climax\",\"resolved ending\"]}}. The acts array MUST contain six strings describing specific causal events. The ending must resolve the premise. Suitable for a single narrator reading dialogue and action. Preserve the supplied character description unchanged.", 3500)
                if isinstance(candidate.get("acts"), list) and len(candidate["acts"]) == 6 and all(isinstance(a, str) and a.strip() for a in candidate["acts"]) and isinstance(candidate.get("character_bible"), str) and candidate["character_bible"].strip():
                    plan = candidate
                    break
            if plan is None:
                raise RuntimeError("The writer returned an incomplete story outline after two attempts. Choose another writer provider or retry production.")
            if cache:
                (cache / "outline.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        self.guard.approve({"premise": topic, "required_character": character_anchor, "outline": plan}, {"canon": "Does this outline preserve every supplied character trait unchanged and define a consistent cast?", "story": "Does this outline causally resolve the requested premise with a coherent beginning, middle and ending?"}, cache / "outline_review.json" if cache else None)
        shots = json.loads((cache / "draft.json").read_text(encoding="utf-8")) if cache and (cache / "draft.json").exists() else []
        saved_count = len(shots)
        if saved_count > count:
            raise ContinuityError("Saved draft has more scenes than this project permits.")
        for start in range(len(shots), count, 6):
            end = min(count, start + 6)
            word_limit = max(8, int(scene_duration * 2.6))
            instruction = f"STORY PLAN: {json.dumps(plan, ensure_ascii=False)}\nOriginal premise: {topic}\nStyle: {style}. This is ONE film with {count} scenes. Write exactly scenes {start + 1} through {end}, in order. Each scene lasts {scene_duration:.2f} seconds. Move through all six acts in proportion to scene position; the final scene must finish the resolved ending. Previous scenes: {json.dumps(shots[-3:], ensure_ascii=False)}. REQUIRED FIRST START STATE: {json.dumps(shots[-1].get("end_state") if shots else None)}\nReturn {{\"shots\":[{{\"title\":\"specific scene title\",\"prompt\":\"visually specific single anime END-OF-SCENE frame depicting end_state, with the exact recurring character descriptions, location, action and camera framing\",\"narration\":\"English narration including spoken dialogue, between {max(4, word_limit - 8)} and {word_limit} words\",\"framing\":\"wide or close-up\"}}]}}. Do not repeat earlier narration. No stage directions in narration. Keep narration within its word budget. No missing scenes. Each shot must also include start_state and end_state strings describing location, cast positions, possessions and ongoing action. Its start_state must exactly repeat the previous shot end_state, then advance the action in end_state. First scene invents an opening state. No jumps in location, time, costume or identity."
            batch = None
            for attempt in range(2):
                result = self.request(instruction + ("\nYour previous batch was incomplete or over the narration word limit. Correct every scene." if attempt else ""))
                candidates = result.get("shots")
                if isinstance(candidates, list) and len(candidates) == end - start and all(isinstance(s, dict) and isinstance(s.get("prompt"), str) and s["prompt"].strip() and isinstance(s.get("narration"), str) and 1 <= len(s["narration"].split()) <= word_limit + 3 for s in candidates):
                    try:
                        previous = shots[-1].get("end_state") if shots else None
                        for position, shot in enumerate(candidates):
                            if not isinstance(shot.get("start_state"), str) or not shot["start_state"].strip() or not isinstance(shot.get("end_state"), str) or not shot["end_state"].strip():
                                raise ContinuityError("Writer omitted explicit scene handoff states.")
                            if previous is not None and shot["start_state"] != previous:
                                raise ContinuityError("Writer changed the previous ending at the next beginning.")
                            self.guard.approve({"canon": plan["character_bible"], "previous_end_state": previous, "scene": shot}, {"identity": "Does the prompt and narration preserve the exact character identity, appearance, outfit and accessories defined by canon?", "handoff": "Does this scene continue the supplied previous ending without teleporting, resetting events, changing possessions or contradicting physical state, and does its end_state follow its narrated action?"}, cache / f"script_review_{start+position+1:04d}.json" if cache else None)
                            previous = shot["end_state"]
                    except ContinuityError as exc:
                        if attempt == 1:
                            raise
                        instruction += "\nRejected continuity: " + str(exc) + ". Rewrite this entire batch with exact handoffs."
                        continue
                    batch = candidates
                    break
            if batch is None:
                raise RuntimeError(f"Writer could not produce valid narration for scenes {start + 1}–{end}. Retry or choose another writer provider.")
            for shot in batch:
                shot.update(id=len(shots) + 1, duration=scene_durations[len(shots)], motion="zoom_in" if len(shots) % 2 == 0 else "zoom_out")
                shots.append(shot)
            if cache:
                temporary = cache / "draft.tmp"
                temporary.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")
                temporary.replace(cache / "draft.json")
            if callback:
                callback(f"Writer: Completed {end}/{count} scenes...")
        previous = None
        for index, shot in enumerate(shots):
            if not shot.get("start_state") or not shot.get("end_state") or (previous is not None and shot["start_state"] != previous):
                raise ContinuityError("Saved screenplay lacks verified scene handoffs. Start a new project; old independent scenes cannot be resumed under strict continuity.")
            if index < saved_count:
                if abs(float(shot.get("duration", 0)) - scene_durations[index]) > .001:
                    raise ContinuityError("Saved scene timing differs from this project's frame schedule.")
                self.guard.approve({"canon": plan["character_bible"], "scene": shot, "previous_end_state": previous}, {"consistency": "Does this scene preserve canonical character identity and continue exactly from the prior ending with coherent narration and physical state?"})
            previous = shot["end_state"]
        return {"success": True, "provider": "story_writer+structured_review", "title": plan.get("title", "Anime Story"), "topic": topic, "genre": style, "targetDuration": duration, "character_bible": plan["character_bible"], "acts": plan["acts"], "shots": shots, "scriptText": "\n\n".join(s["narration"] for s in shots)}
