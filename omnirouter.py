import os
import sys
import time
import json
import logging
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="[OmniRouter] %(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OmniRouter")


MASTER_STYLE_GUIDE_PROMPT = """
YOU ARE THE MASTER ANIMATION SCRIPT & SHOT LIST GENERATOR FOR OPEN DRAMA ENGINE v2.0.

### 2D CARTOON STYLE GUIDES & CINEMATOGRAPHY RULES
1. Visual Style: High-energy 2D animated cartoon/anime style with clean line-art, vibrant cell-shading, dynamic camera angles, and expressive character poses.
2. Camera Framing Schemas:
   - CU Dialogue: Close-Up shot focusing on character facial expressions during speech or dialogue.
   - Wide Action: Extreme Wide or Wide Tracking shot capturing environment, motion, hovercars, and action sequences.
   - Medium Tracking: Medium waist-up tracking shot following a character moving through the environment.
   - Over the Shoulder: OTS framing establishing spatial relationships between two characters or a character and a threat.
   - Close-Up: Tight framing on key props, tools, or reaction faces.
   - Extreme Wide: Establishing shot of the city, landscape, or environment.

### STRUCTURED RESPONSE SCHEMA
Return ONLY a valid JSON object with no extra markdown or explanations:
{
  "topic": "string",
  "genre": "string",
  "targetDuration": 30,
  "scriptText": "formatted scene script string",
  "shots": [
    {
      "id": 1,
      "title": "Shot 01: ...",
      "prompt": "Detailed 2D cartoon anime style prompt for keyframe generation",
      "framing": "CU Dialogue",
      "duration": 5.0
    }
  ]
}
"""


class GeminiPromptCacheManager:
    """Manages Google GenAI Context Caching for system instructions."""

    def __init__(self, ttl_seconds=600):
        self.ttl_seconds = ttl_seconds
        self.cached_content_name = None
        self.expiration_time = 0
        self.client = None

    def get_client(self, api_key):
        if not self.client and api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai Client: {e}")
        return self.client

    def get_or_create_cache(self, api_key, model="gemini-2.5-flash"):
        client = self.get_client(api_key)
        if not client:
            return None

        now = time.time()
        if self.cached_content_name and now < (self.expiration_time - 30):
            return self.cached_content_name

        try:
            config = types.CreateCachedContentConfig(
                contents=[MASTER_STYLE_GUIDE_PROMPT],
                ttl=f"{self.ttl_seconds}s",
                display_name="open_drama_master_style_guide"
            )
            cache = client.caches.create(model=model, config=config)
            self.cached_content_name = cache.name
            self.expiration_time = now + self.ttl_seconds
            return self.cached_content_name
        except Exception as err:
            logger.warning(f"Context Caching failed ({err}).")
            return None


STAGE_PRIORITY_MATRIX = {
    "scripting": {
        "chain": ["omniroute", "gemini", "openrouter"],
        "timeout": 15
    },
    "asset_prompts": {
        "chain": ["fal", "comfyui"],
        "timeout": 20
    },
    "timeline_assembly": {
        "chain": ["omniroute", "gemini", "openrouter"],
        "timeout": 10
    }
}


class OmniRouter:
    """
    Automated Multi-Provider API Router for Open Drama Engine:
    OmniRoute (Scripts) -> Fal.ai API / Local ComfyUI (Images) -> Local Fallback Guard
    """

    def __init__(self, workspace_dir=None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.output_dir = self.workspace_dir / "generated_assets"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_manager = GeminiPromptCacheManager(ttl_seconds=600)
        self.omniroute_base_url = os.getenv("OMNI_BASE_URL", "http://localhost:20128/v1")
        self.comfyui_base_url = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188")

        self._refresh_keys()

    def _refresh_keys(self):
        """Discovers and caches API keys from environment variables."""
        self.keys = {
            "gemini": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "omniroute": os.getenv("OMNI_API_KEY") or os.getenv("OMNIROUTE_API_KEY"),
            "fal": os.getenv("FAL_KEY") or os.getenv("FAL_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
        }

    def get_provider_status(self):
        """Returns availability status for all integrated providers."""
        self._refresh_keys()
        return {
            "gemini": {"configured": bool(self.keys["gemini"]), "type": "Gemini API"},
            "omniroute": {"configured": bool(self.keys["omniroute"]), "type": "Local OmniRoute Proxy"},
            "fal": {"configured": bool(self.keys["fal"]), "type": "Fal.ai API (FAL_KEY)"},
            "comfyui": {"configured": self._check_comfyui_online(), "type": "Local ComfyUI Server (100% Free)"},
            "local_fallback": {"configured": True, "type": "PIL Synthetic Keyframe Renderer"},
            "stage_priority_matrix": STAGE_PRIORITY_MATRIX
        }

    def _check_comfyui_online(self):
        """Checks if local ComfyUI server is reachable."""
        try:
            res = requests.get(f"{self.comfyui_base_url}/system_stats", timeout=3)
            return res.status_code == 200
        except Exception:
            return False

    def _get_available_checkpoint(self):
        """Queries ComfyUI to discover installed checkpoint model files."""
        try:
            res = requests.get(f"{self.comfyui_base_url}/object_info/CheckpointLoaderSimple", timeout=5)
            if res.status_code == 200:
                ckpts = res.json()["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
                if "DreamShaper_8_pruned.safetensors" in ckpts:
                    return "DreamShaper_8_pruned.safetensors"
                if "v1-5-pruned-emaonly.safetensors" in ckpts:
                    return "v1-5-pruned-emaonly.safetensors"
                if len(ckpts) > 0:
                    return ckpts[0]
        except Exception as e:
            logger.warning(f"Could not query ComfyUI checkpoints ({e}).")
        return "DreamShaper_8_pruned.safetensors"

    def generate_script(self, topic, genre="2D Cartoon Action", target_duration=30):
        """Generates scene script and shot list using OmniRoute or Gemini."""
        logger.info(f"✨ Generating AI Script for topic: '{topic[:40]}...' ({genre}, {target_duration}s)")
        target_duration = int(target_duration)

        self._refresh_keys()
        omni_key = self.keys.get("omniroute")
        gemini_key = self.keys.get("gemini")

        if omni_key:
            try:
                url = f"{self.omniroute_base_url}/chat/completions"
                headers = {"Authorization": f"Bearer {omni_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gemini-2.5-flash",
                    "messages": [
                        {"role": "system", "content": MASTER_STYLE_GUIDE_PROMPT},
                        {"role": "user", "content": f"Topic: {topic}\nGenre: {genre}\nTarget Duration: {target_duration}s"}
                    ],
                    "response_format": {"type": "json_object"}
                }
                response = requests.post(url, headers=headers, json=payload, timeout=20)
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    parsed["success"] = True
                    return parsed
            except Exception as err:
                logger.warning(f"OmniRoute script call failed ({err}).")

        if gemini_key and GENAI_AVAILABLE:
            try:
                cache_name = self.cache_manager.get_or_create_cache(gemini_key)
                client = self.cache_manager.get_client(gemini_key)
                config = types.GenerateContentConfig(
                    cached_content=cache_name,
                    system_instruction=MASTER_STYLE_GUIDE_PROMPT if not cache_name else None,
                    response_mime_type="application/json"
                )
                response = client.models.generate_content(model="gemini-2.5-flash", contents=f'Topic: "{topic}"', config=config)
                if response and response.text:
                    parsed = json.loads(response.text)
                    parsed["success"] = True
                    return parsed
            except Exception as err:
                logger.warning(f"Gemini direct call failed ({err}).")

        num_shots = max(2, min(12, int(target_duration / 5)))
        shots = [{"id": i + 1, "title": f"Shot {i+1:02d}", "prompt": f"2D anime style shot for {topic}", "framing": "Wide Action", "duration": 5.0} for i in range(num_shots)]
        return {"success": True, "topic": topic, "genre": genre, "targetDuration": target_duration, "scriptText": f"SCRIPT: {topic}", "shots": shots}

    def generate_image(self, prompt, negative_prompt="", aspect_ratio="16:9", preferred_provider=None, privacy_mode=False):
        """Generates keyframe image via Fal.ai -> Local ComfyUI -> PIL Fallback."""
        self._refresh_keys()
        width, height = self._parse_aspect_ratio(aspect_ratio)

        if privacy_mode:
            return self._generate_local_synthetic_keyframe(prompt, aspect_ratio, width, height)

        # 1. Try Fal.ai API if key is present
        fal_key = self.keys.get("fal")
        if fal_key and FAL_AVAILABLE:
            try:
                logger.info("🎨 Generating image via Fal.ai API...")
                os.environ["FAL_KEY"] = fal_key
                result = fal_client.subscribe(
                    "fal-ai/flux/schnell",
                    arguments={"prompt": prompt, "image_size": {"width": width, "height": height}}
                )
                if result and "images" in result and len(result["images"]) > 0:
                    image_url = result["images"][0]["url"]
                    img_data = requests.get(image_url).content
                    file_path = self.output_dir / f"fal_{int(time.time()*1000)}.png"
                    with open(file_path, "wb") as f:
                        f.write(img_data)
                    return {"success": True, "provider": "fal", "image_path": str(file_path), "url": str(file_path)}
            except Exception as err:
                logger.warning(f"Fal.ai generation failed ({err}). Routing to next provider...")

        # 2. Try Local ComfyUI Server if active
        if self._check_comfyui_online():
            try:
                logger.info("🎨 Generating image via Local ComfyUI Server...")
                return self._call_comfyui_image(prompt, width, height)
            except Exception as err:
                logger.warning(f"ComfyUI generation failed ({err}). Routing to local fallback...")

        # 3. Safe Local Fallback
        return self._generate_local_synthetic_keyframe(prompt, aspect_ratio, width, height)

    def _call_comfyui_image(self, prompt, width, height):
        """Sends workflow payload to local ComfyUI instance with extended polling timeout."""
        ckpt_name = self._get_available_checkpoint()
        logger.info(f"Using ComfyUI Checkpoint: '{ckpt_name}'")

        workflow = {
            "3": {"inputs": {"seed": int(time.time()), "steps": 20, "cfg": 8, "sampler_name": "euler", "scheduler": "normal", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
            "4": {"inputs": {"ckpt_name": ckpt_name}, "class_type": "CheckpointLoaderSimple"},
            "5": {"inputs": {"width": width, "height": height, "batch_size": 1}, "class_type": "EmptyLatentImage"},
            "6": {"inputs": {"text": prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
            "7": {"inputs": {"text": "text, watermark, low quality, blurry", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
            "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
            "9": {"inputs": {"filename_prefix": "ODE_Keyframe", "images": ["8", 0]}, "class_type": "SaveImage"}
        }

        res = requests.post(f"{self.comfyui_base_url}/prompt", json={"prompt": workflow}, timeout=30)
        if res.status_code == 200:
            prompt_id = res.json().get("prompt_id")
            # Poll up to 180 seconds to allow cold VRAM model loading on GTX 1660 SUPER
            for _ in range(180):
                time.sleep(1)
                try:
                    hist_res = requests.get(f"{self.comfyui_base_url}/history/{prompt_id}", timeout=5)
                    if hist_res.status_code == 200 and prompt_id in hist_res.json():
                        outputs = hist_res.json()[prompt_id].get("outputs", {})
                        if "9" in outputs and "images" in outputs["9"]:
                            img_info = outputs["9"]["images"][0]
                            img_res = requests.get(f"{self.comfyui_base_url}/view", params=img_info, timeout=30)
                            file_path = self.output_dir / f"comfy_{int(time.time()*1000)}.png"
                            with open(file_path, "wb") as f:
                                f.write(img_res.content)
                            return {"success": True, "provider": "comfyui", "image_path": str(file_path), "url": str(file_path)}
                except Exception:
                    pass
        raise Exception("ComfyUI execution timed out or failed.")

    def _generate_local_synthetic_keyframe(self, prompt, aspect_ratio, width, height):
        img = Image.new("RGB", (width, height), color=(14, 18, 24))
        draw = ImageDraw.Draw(img)

        for y in range(height):
            r = int(14 + (y / height) * 20)
            g = int(18 + (y / height) * 25)
            b = int(24 + (y / height) * 40)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        draw.rectangle([20, 20, width - 20, height - 20], outline=(240, 180, 50), width=2)
        try:
            font_title = ImageFont.truetype("arial.ttf", 36)
            font_sub = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        clean_prompt = prompt[:70] + "..." if len(prompt) > 70 else prompt
        draw.text((45, height // 2 - 40), f'"{clean_prompt}"', fill=(240, 245, 255), font=font_title)
        draw.text((45, height // 2 + 20), f"Aspect: {aspect_ratio} ({width}x{height}) | Provider: Local Fallback", fill=(140, 160, 195), font=font_sub)

        file_path = self.output_dir / f"keyframe_local_{int(time.time()*1000)}.png"
        img.save(file_path)
        return {"success": True, "provider": "local_fallback", "image_path": str(file_path), "url": str(file_path), "fallback": True}

    def _parse_aspect_ratio(self, ratio_str):
        if ratio_str == "9:16":
            return (720, 1280)
        elif ratio_str == "1:1":
            return (1080, 1080)
        return (1280, 720)


if __name__ == "__main__":
    router = OmniRouter()
    print("Provider Status:", json.dumps(router.get_provider_status(), indent=2))
