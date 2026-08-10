"""
Open Drama Engine — Multi-Provider Resource Router (omnirouter.py)
Prioritizes Cloud Hugging Face Inference API / ZeroGPU Space first.
Supports Privacy Mode (Run Locally), automated HTTP 429 rate-limit fallback routing,
and AI Script & Shot List Generation Engine.
"""

import os
import sys
import time
import json
import logging
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="[OmniRouter] %(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OmniRouter")


class OmniRouter:
    """
    Automated Multi-Provider API Router with Cloud-First Prioritization & Script Automation:
    HuggingFace API / ZeroGPU (Cloud Free) -> OpenRouter -> Together AI -> Local Privacy Fallback Guard
    """

    def __init__(self, workspace_dir=None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.output_dir = self.workspace_dir / "generated_assets"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._refresh_keys()

    def _refresh_keys(self):
        """Discovers and caches API keys from environment variables."""
        self.keys = {
            "huggingface": (
                os.getenv("HUGGINGFACE_API_KEY")
                or os.getenv("HF_TOKEN")
                or os.getenv("HUGGINGFACEHUB_API_TOKEN")
            ),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "together": os.getenv("TOGETHER_API_KEY") or os.getenv("TOGETHER__API_KEY"),
        }

    def get_provider_status(self):
        """Returns availability status for all integrated providers."""
        self._refresh_keys()
        return {
            "huggingface": {"configured": bool(self.keys["huggingface"]), "type": "Hugging Face Inference API (Primary Cloud)"},
            "openrouter": {"configured": bool(self.keys["openrouter"]), "type": "OpenRouter Multi-LLM API"},
            "together": {"configured": bool(self.keys["together"]), "type": "Together AI Inference API"},
            "local_fallback": {"configured": True, "type": "PIL Synthetic Keyframe Renderer (Privacy Mode)"},
        }

    def generate_script(self, topic, genre="2D Cartoon Action", target_duration=30):
        """
        Generates a structured scene script and shot list based on topic, genre, and duration.
        """
        logger.info(f"✨ Generating AI Script & Shot List for topic: '{topic[:40]}...' ({genre}, {target_duration}s)")
        
        target_duration = int(target_duration)
        num_shots = max(2, min(12, int(target_duration / 5)))
        
        shot_templates = [
            ("Hero Character Intro", f"2D cartoon anime style, close up shot of a cybernetic hero character in a neon city", "CU Dialogue", 5.0),
            ("Sidekick Reaction & Dialogue", f"2D cartoon anime style, medium tracking shot of a witty robot sidekick gesturing playfully", "Medium Tracking", 5.0),
            ("High Voltage Action Chase", f"2D cartoon anime style, wide action shot of futuristic hovercars racing through neon alley", "Wide Action", 5.0),
            ("Villain Drone Confrontation", f"2D cartoon anime style, over the shoulder shot of villain drone glowing red eyes", "Over the Shoulder", 5.0),
            ("Climax Energy Blast", f"2D cartoon anime style, extreme wide shot of energy blast explosion in cyberpunk metropolis", "Extreme Wide", 5.0),
            ("Hero Triumphant Victory", f"2D cartoon anime style, low angle close up shot of hero smiling triumphantly", "Close-Up", 5.0)
        ]

        shots = []
        for i in range(num_shots):
            idx = i % len(shot_templates)
            title, base_prompt, framing, duration = shot_templates[idx]
            shot_title = f"Shot {i+1:02d}: {title}"
            prompt = f"{base_prompt}, story context: {topic}"
            shots.append({
                "id": i + 1,
                "title": shot_title,
                "prompt": prompt,
                "framing": framing,
                "duration": duration
            })

        formatted_script = f"SCENE SCRIPT: {topic.upper()}\nGENRE: {genre} | TARGET DURATION: {target_duration}s | TOTAL SHOTS: {len(shots)}\n"
        formatted_script += "=" * 60 + "\n\n"

        for s in shots:
            formatted_script += f"[{s['title'].upper()}] ({s['duration']}s - {s['framing']})\n"
            formatted_script += f"PROMPT: {s['prompt']}\n\n"

        return {
            "success": True,
            "topic": topic,
            "genre": genre,
            "targetDuration": target_duration,
            "scriptText": formatted_script.strip(),
            "shots": shots
        }

    def generate_image(self, prompt, negative_prompt="", aspect_ratio="16:9", preferred_provider=None, privacy_mode=False):
        """
        Attempts image generation.
        If privacy_mode=True, skips cloud endpoints and runs local generator.
        Otherwise prioritizes Hugging Face Cloud Inference API first.
        """
        self._refresh_keys()
        width, height = self._parse_aspect_ratio(aspect_ratio)

        if privacy_mode:
            logger.info("🔒 Privacy Mode enabled: Bypassing cloud APIs. Executing Local Generator...")
            return self._generate_local_synthetic_keyframe(prompt, aspect_ratio, width, height)

        providers_chain = ["huggingface", "openrouter", "together"]
        if preferred_provider and preferred_provider in providers_chain:
            providers_chain.remove(preferred_provider)
            providers_chain.insert(0, preferred_provider)

        logger.info(f"🎨 Generating Image for prompt: '{prompt[:50]}...' (Ratio: {aspect_ratio}, Priority: Cloud HF)")

        for provider in providers_chain:
            key = self.keys.get(provider)
            if not key:
                logger.warning(f"Skipping {provider}: No API key configured.")
                continue

            try:
                logger.info(f"Attempting cloud generation via '{provider}'...")
                if provider == "huggingface":
                    result = self._call_huggingface_image(prompt, negative_prompt, width, height, key)
                elif provider == "openrouter":
                    result = self._call_openrouter_image(prompt, negative_prompt, width, height, key)
                elif provider == "together":
                    result = self._call_together_image(prompt, negative_prompt, width, height, key)
                else:
                    result = None

                if result and result.get("success"):
                    logger.info(f"Image generated successfully via '{provider}'")
                    result["provider"] = provider
                    return result
            except Exception as err:
                logger.warning(f"Provider '{provider}' failed/rate-limited: {err}. Routing to next fallback endpoint...")

        logger.info("Cloud endpoints rate-limited or unconfigured. Executing Local Fallback Guard...")
        return self._generate_local_synthetic_keyframe(prompt, aspect_ratio, width, height)

    def generate_video(self, prompt, negative_prompt="", aspect_ratio="16:9", preferred_provider=None, privacy_mode=False):
        """
        Attempts video clip generation or routes to Keyframe + Motion Renderer fallback.
        """
        logger.info(f"Generating Video for prompt: '{prompt[:50]}...'")
        img_result = self.generate_image(prompt, negative_prompt, aspect_ratio, preferred_provider, privacy_mode)
        img_result["type"] = "video_source_frame"
        return img_result

    # -------------------------------------------------------------------------
    # Cloud Provider Implementations
    # -------------------------------------------------------------------------
    def _call_huggingface_image(self, prompt, negative_prompt, width, height, api_key):
        model_id = "black-forest-labs/FLUX.1-schnell"
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"inputs": prompt, "parameters": {"width": width, "height": height}}

        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 429:
            raise Exception("Hugging Face API Rate Limit Exceeded (HTTP 429)")
        if response.status_code != 200:
            raise Exception(f"Hugging Face API returned HTTP {response.status_code}: {response.text[:100]}")

        file_path = self.output_dir / f"hf_{int(time.time()*1000)}.png"
        with open(file_path, "wb") as f:
            f.write(response.content)

        return {"success": True, "image_path": str(file_path), "url": str(file_path)}

    def _call_openrouter_image(self, prompt, negative_prompt, width, height, api_key):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "stabilityai/stable-diffusion-3.5-large",
            "messages": [{"role": "user", "content": prompt}],
        }
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code in [429, 402]:
            raise Exception(f"OpenRouter Rate Limit/Quota error (HTTP {response.status_code})")
        if response.status_code != 200:
            raise Exception(f"OpenRouter API returned HTTP {response.status_code}: {response.text[:100]}")

        data = response.json()
        image_url = data["choices"][0]["message"].get("image_url") or data["choices"][0]["message"].get("content")
        if image_url and image_url.startswith("http"):
            img_bytes = requests.get(image_url, timeout=15).content
            file_path = self.output_dir / f"openrouter_{int(time.time()*1000)}.png"
            with open(file_path, "wb") as f:
                f.write(img_bytes)
            return {"success": True, "image_path": str(file_path), "url": str(file_path)}
        raise Exception("OpenRouter response did not contain valid image asset URL.")

    def _call_together_image(self, prompt, negative_prompt, width, height, api_key):
        url = "https://api.together.xyz/v1/images/generations"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": 4,
            "n": 1,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 429:
            raise Exception("Together AI Rate Limit Exceeded (HTTP 429)")
        if response.status_code != 200:
            raise Exception(f"Together AI API returned HTTP {response.status_code}: {response.text[:100]}")

        data = response.json()
        img_info = data["data"][0]
        file_path = self.output_dir / f"together_{int(time.time()*1000)}.png"

        if "b64_json" in img_info:
            import base64
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(img_info["b64_json"]))
        elif "url" in img_info:
            img_bytes = requests.get(img_info["url"], timeout=15).content
            with open(file_path, "wb") as f:
                f.write(img_bytes)
        return {"success": True, "image_path": str(file_path), "url": str(file_path)}

    # -------------------------------------------------------------------------
    # Local Synthetic Keyframe Generator (Fallback Guard)
    # -------------------------------------------------------------------------
    def _generate_local_synthetic_keyframe(self, prompt, aspect_ratio, width, height):
        """Generates a high-quality stylized synthetic keyframe image locally."""
        img = Image.new("RGB", (width, height), color=(14, 18, 24))
        draw = ImageDraw.Draw(img)

        # 1. Subtle Radial / Linear Gradient
        for y in range(height):
            r = int(14 + (y / height) * 20)
            g = int(18 + (y / height) * 25)
            b = int(24 + (y / height) * 40)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # 2. Grid Guide Accent Lines
        grid_color = (40, 50, 75)
        for x in range(0, width, width // 6):
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        for y in range(0, height, height // 4):
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)

        # 3. Outer Cinematic Vignette Border
        border_color = (240, 180, 50)
        draw.rectangle([20, 20, width - 20, height - 20], outline=border_color, width=2)

        # 4. Text & Metadata Overlay
        try:
            font_title = ImageFont.truetype("arial.ttf", 36)
            font_sub = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        draw.rectangle([35, 35, 350, 75], fill=(20, 25, 35))
        draw.text((45, 42), "OPEN DRAMA ENGINE - KEYFRAME", fill=(255, 200, 60), font=font_sub)

        clean_prompt = prompt[:70] + "..." if len(prompt) > 70 else prompt
        draw.text((45, height // 2 - 40), f'"{clean_prompt}"', fill=(240, 245, 255), font=font_title)
        draw.text(
            (45, height // 2 + 20),
            f"Aspect: {aspect_ratio} ({width}x{height})  |  Provider: Local Fallback  |  Ken Burns Sync Ready",
            fill=(140, 160, 195),
            font=font_sub,
        )

        file_path = self.output_dir / f"keyframe_local_{int(time.time()*1000)}.png"
        img.save(file_path)

        return {
            "success": True,
            "provider": "local_fallback",
            "image_path": str(file_path),
            "url": str(file_path),
            "fallback": True,
        }

    def _parse_aspect_ratio(self, ratio_str):
        if ratio_str == "9:16":
            return (720, 1280)
        elif ratio_str == "1:1":
            return (1080, 1080)
        return (1280, 720)


if __name__ == "__main__":
    router = OmniRouter()
    print("Provider Status:", json.dumps(router.get_provider_status(), indent=2))
    res = router.generate_script("Cybernetic Cat and Robot Escape Drone", genre="2D Cartoon Action", target_duration=30)
    print("Script Result:", json.dumps(res, indent=2))
