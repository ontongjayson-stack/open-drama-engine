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

# =============================================================================
# 15 VISUAL STYLE PRESETS (SD 1.5 Optimized Modifiers & Negative Tags)
# =============================================================================
STYLE_PRESETS = {
    "Disney 3.0": {
        "name": "Disney 3.0",
        "icon": "✨",
        "badge": "Family & Magic",
        "description": "Magical 3D animated character style with expressive eyes, warm lighting, and lush Disney charm.",
        "prompt_modifier": "disney 3.0 3d animation style, pixar render, highly detailed expressive character, subsurface scattering, vibrant warm studio lighting, 8k resolution, smooth 3d animation, cute appealing aesthetic",
        "negative_modifier": "blurry, low quality, static, distorted, deformed hands, bad anatomy, realistic photo, gritty, dark, artifacts, watermark, text"
    },
    "Anime": {
        "name": "Anime",
        "icon": "⚡",
        "badge": "Action & Shonen",
        "description": "Vibrant Japanese anime style with clean cel-shading, dynamic linework, and high-contrast lighting.",
        "prompt_modifier": "high quality Japanese anime aesthetic, vibrant cel shading, makoto shinkai style, clean crisp lineart, dramatic anime studio lighting, detailed background, dynamic pose, 1080p anime keyframe",
        "negative_modifier": "3d render, western cartoon, photorealistic, blurry, low resolution, deformed limbs, bad eyes, poorly drawn face, text, signature"
    },
    "3D Cartoon": {
        "name": "3D Cartoon",
        "icon": "🧸",
        "badge": "Playful & Bold",
        "description": "Whimsical toy-like clay 3D animation with soft ambient occlusion and bright playful colors.",
        "prompt_modifier": "charming 3d cartoon character animation, smooth stylized clay textures, bright whimsical color palette, soft ambient occlusion, toy-like tactile render, cinema 4d octane render style",
        "negative_modifier": "grungy, dark, realistic skin pores, photorealistic, uncanny valley, blurry, low quality, noisy, artifacts"
    },
    "Realistic": {
        "name": "Realistic",
        "icon": "🎥",
        "badge": "Cinematic 35mm",
        "description": "Photorealistic live-action cinema look with natural dramatic lighting and shallow depth of field.",
        "prompt_modifier": "cinematic film still, 35mm photograph, shot on Arri Alexa, photorealistic, natural dramatic lighting, shallow depth of field, 8k resolution, hyperrealistic textures, masterpiece",
        "negative_modifier": "cartoon, 3d render, anime, illustration, painting, drawing, plastic skin, blurry, oversaturated, watermark, bad hands"
    },
    "Cyberpunk 2077": {
        "name": "Cyberpunk 2077",
        "icon": "🏙️",
        "badge": "Sci-Fi Neon",
        "description": "Rain-slicked neon skyscrapers, glowing holographic billboards, volumetric haze, and chromatic aberration.",
        "prompt_modifier": "cyberpunk 2077 aesthetic, neon drenched rain-slicked city, glowing holographic advertisements, volumetric fog, chromatic aberration, futuristic high tech gear, raytracing reflections",
        "negative_modifier": "pastoral, medieval, cartoon, blurry, low quality, washed out colors, daytime sunlight, bad anatomy, flat lighting"
    },
    "Retro 80s Synthwave": {
        "name": "Retro 80s Synthwave",
        "icon": "📼",
        "badge": "Outrun Neon",
        "description": "Retro-futuristic purple and magenta wireframes, glowing neon horizons, and nostalgic 80s VHS tape vibes.",
        "prompt_modifier": "retro 80s synthwave neon aesthetic, outrun magenta and cyan wireframe grid, glowing laser lines, retrofuturism, CRT scanlines, sunset horizon, 1980s VHS tape movie vibe",
        "negative_modifier": "modern photorealism, monochrome, washed out, blurry, modern minimalism, deformed characters, low contrast"
    },
    "Pixel Art 16-Bit": {
        "name": "Pixel Art 16-Bit",
        "icon": "👾",
        "badge": "Retro Gaming",
        "description": "Classic 16-bit SNES JRPG sprite art with crisp pixel palettes and nostalgic retro dithering.",
        "prompt_modifier": "16-bit pixel art style, crisp pixel sprites, classic SNES JRPG aesthetic, vibrant pixelated palette, clean dithering, nostalgic video game screen, master pixel artist",
        "negative_modifier": "smooth gradients, 3d render, vector art, high resolution photograph, blurry, anti-aliasing blur, realistic"
    },
    "Claymation": {
        "name": "Claymation",
        "icon": "🧱",
        "badge": "Stop-Motion",
        "description": "Tactile plasticine clay stop-motion puppets with subtle thumbprint marks and miniature studio lighting.",
        "prompt_modifier": "stop motion claymation style, tactile plasticine clay textures, Aardman animations aesthetic, subtle thumbprint marks, studio softbox miniature lighting, physical stop-motion puppet",
        "negative_modifier": "smooth digital 3d, flat 2d cartoon, photorealistic human, glossy, blurry, digital vector, oversaturated"
    },
    "Comic Book": {
        "name": "Comic Book",
        "icon": "💥",
        "badge": "Graphic Novel",
        "description": "Bold ink linework, retro Ben-Day halftone dot patterns, and punchy pop-art action comic frames.",
        "prompt_modifier": "classic comic book art style, bold ink lineart, retro ben-day halftone dots, dramatic dynamic action shadows, vibrant pop art colors, graphic novel cover illustration",
        "negative_modifier": "photorealistic, smooth 3d cgi, soft watercolor, blurry, washed out, low contrast, noise"
    },
    "Dark Fantasy": {
        "name": "Dark Fantasy",
        "icon": "⚔️",
        "badge": "Elden Lore",
        "description": "Grimdark gothic atmosphere, swirling golden embers, weathered armor, and moody cinematic fog.",
        "prompt_modifier": "dark fantasy aesthetic, Elden Ring style, moody gothic atmosphere, floating golden embers, ancient weathered stone, dramatic volumetric fog, dark souls cinematic mood",
        "negative_modifier": "bright whimsical cartoon, cheerful, neon, oversaturated, low quality, bad hands, blurry, flat lighting"
    },
    "Pixar Studio 3D": {
        "name": "Pixar Studio 3D",
        "icon": "🎈",
        "badge": "Heartwarming",
        "description": "Emotional Pixar feature animation styling, soft global illumination, and rich storytelling aesthetics.",
        "prompt_modifier": "Pixar feature film animation style, expressive emotive eyes, soft subsurface scattering, warm cinematic lighting, whimsical character design, render engine quality, heartwarming atmosphere",
        "negative_modifier": "harsh shadows, gritty realism, bad geometry, anime, flat 2d, distorted face, lowres, dark horror"
    },
    "Watercolor Storybook": {
        "name": "Watercolor Storybook",
        "icon": "🎨",
        "badge": "Fable & Wonder",
        "description": "Gentle hand-painted storybook illustrations with soft pigment bleeds and delicate pencil sketches.",
        "prompt_modifier": "children's storybook illustration, delicate watercolor painting, soft bleeding pigment edges, whimsical pencil sketch outlines, gentle pastel color palette, textured paper",
        "negative_modifier": "harsh black lines, 3d cgi, photorealistic, neon glow, sharp digital renders, oversaturated, dark"
    },
    "Noir Detective": {
        "name": "Noir Detective",
        "icon": "🕵️",
        "badge": "Classic Film Noir",
        "description": "1940s black-and-white high-contrast chiaroscuro shadows, venetian blinds, and smoky urban alleys.",
        "prompt_modifier": "1940s film noir cinema, black and white monochrome photography, high contrast chiaroscuro lighting, venetian blind shadows, cigarette smoke atmosphere, gritty detective thriller",
        "negative_modifier": "color, colorful, cartoon, anime, bright daylight, saturated colors, low contrast, washed out, blurry"
    },
    "Studio Ghibli": {
        "name": "Studio Ghibli",
        "icon": "🍃",
        "badge": "Pastoral Whimsy",
        "description": "Hayao Miyazaki inspired painted landscapes, fluffy summer clouds, and nostalgic hand-drawn warmth.",
        "prompt_modifier": "Studio Ghibli aesthetic, hand-painted anime landscape, Hayao Miyazaki style, lush green pastoral countryside, fluffy painted cumulus clouds, nostalgic serene atmosphere, rich gouache art",
        "negative_modifier": "dark gritty realism, 3d cgi render, sharp metallic neon, photorealistic, low quality, bad anatomy, harsh edges"
    },
    "Steampunk Victorian": {
        "name": "Steampunk Victorian",
        "icon": "⚙️",
        "badge": "Clockwork",
        "description": "Polished brass machinery, clockwork gears, Victorian gentleman attire, and billowing steam pipes.",
        "prompt_modifier": "intricate steampunk aesthetic, polished brass gears and copper machinery, Victorian industrial design, billowing white steam, vintage sepia and copper tones, clockwork craftsmanship",
        "negative_modifier": "futuristic neon, minimalist modern, flat cartoon, blurry, low resolution, cheap plastic, washed out"
    }
}

def expand_prompt_with_style(prompt_text: str, style_name: str = "Disney 3.0") -> tuple:
    """Combines a base story prompt with the selected visual style modifiers for SD 1.5."""
    preset = STYLE_PRESETS.get(style_name, STYLE_PRESETS["Disney 3.0"])
    positive = f"{prompt_text.strip()}, {preset['prompt_modifier']}"
    negative = preset["negative_modifier"]
    return positive, negative

def get_available_styles() -> list:
    """Returns a list of all 15 visual styles with display metadata for UI cards."""
    return list(STYLE_PRESETS.values())


# =============================================================================
# MASTER SCRIPTWRITER PROMPT SCHEMA
# =============================================================================
MASTER_STYLE_GUIDE_PROMPT = """
YOU ARE THE MASTER ANIMATION SCRIPTWRITER & DIRECTOR FOR OPEN DRAMA ENGINE.
Generate a concise, high-impact scene breakdown for an animated short film.

Return ONLY a valid JSON object with NO markdown formatting, NO backticks:
{
  "topic": "string",
  "genre": "string",
  "targetDuration": 15,
  "scriptText": "full formatted script dialogue and narration",
  "shots": [
    {
      "id": 1,
      "title": "Scene 01: ...",
      "prompt": "Vivid descriptive visual scene for AI video rendering, describing character, motion, camera angle, and environment",
      "framing": "Wide Action / Close-Up / Tracking",
      "duration": 5.0
    }
  ]
}
"""


def extract_json_object(raw_text: str):
    """Robustly extracts valid JSON object from raw LLM text with markdown, reasoning, or chit-chat."""
    if not raw_text:
        return None
    text = str(raw_text).strip()
    # 1. Strip reasoning tags (<think>...</think>)
    if "<think>" in text and "</think>" in text:
        text = text.split("</think>")[-1].strip()
    elif "<think>" in text:
        text = text.split("<think>")[0].strip()

    # 2. Strip markdown blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # 3. Find outermost { and }
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        candidate = text[start_idx:end_idx + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "shots" in parsed and len(parsed["shots"]) > 0:
                return parsed
        except Exception:
            pass

    # 4. Fallback direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "shots" in parsed and len(parsed["shots"]) > 0:
            return parsed
    except Exception:
        pass
    return None


class OmniRouter:
    """
    100% Free Autonomous API Router for Open Drama Engine:
    - Scripts: OpenRouter Free Models (`openrouter/free`) -> Gemini API -> Structured Fallback
    - Video/Images: Local ComfyUI (127.0.0.1:8188) -> Fal.ai API -> Synthetic Safe Fallback
    """

    def __init__(self, workspace_dir=None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).resolve().parent
        self.output_dir = self.workspace_dir / "generated_assets"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.comfyui_base_url = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188")
        self._refresh_keys()

    def _refresh_keys(self):
        """Discovers and caches API keys from environment variables."""
        try:
            from dotenv import load_dotenv
            load_dotenv(self.workspace_dir / ".env")
        except ImportError:
            pass
        self.keys = {
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "gemini": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "fal": os.getenv("FAL_KEY") or os.getenv("FAL_API_KEY"),
        }

    def get_provider_status(self):
        """Returns availability status for all integrated providers."""
        self._refresh_keys()
        return {
            "continuity_review": {"configured": bool(self.keys["openrouter"] or self.keys["gemini"]), "type": "Skill-guided review using existing generation models"},
            "gemini": {"configured": bool(self.keys["gemini"]), "type": "Gemini writer and visual identity observer"},
            "openrouter_free": {"configured": bool(self.keys["openrouter"]), "type": "OpenRouter free-model screenplay writer"},
            "comfyui": {"configured": self._check_comfyui_online(), "type": "Local ComfyUI Server (127.0.0.1:8188 - 6GB VRAM)"},
            "styles_count": len(STYLE_PRESETS)
        }

    def _check_comfyui_online(self):
        """Checks if local ComfyUI server is reachable."""
        try:
            res = requests.get(f"{self.comfyui_base_url}/system_stats", timeout=3)
            return res.status_code == 200
        except Exception:
            return False

    def generate_script_gemini(self, topic: str, style: str = "Disney 3.0", duration: int = 15, character_anchor: str = "", status_callback=None):
        return self.generate_story(topic, style, duration, character_anchor, "gemini", status_callback)

    def generate_script_openrouter_free(self, topic: str, style: str = "Disney 3.0", duration: int = 15, genre: str = None, target_duration: int = None, character_anchor: str = "", status_callback=None):
        return self.generate_story(topic, genre or style, target_duration if target_duration is not None else duration, character_anchor, "openrouter", status_callback)

    def generate_script(self, topic: str, style: str = "Disney 3.0", duration: int = 15, genre: str = None, target_duration: int = None, character_anchor: str = "", provider: str = "auto", status_callback=None):
        return self.generate_story(topic, genre or style, target_duration if target_duration is not None else duration, character_anchor, provider, status_callback)

    def generate_script_autonomous(self, topic: str, style: str = "Disney 3.0", duration: int = 15, genre: str = None, target_duration: int = None, character_anchor: str = ""):
        return self.generate_story(topic, genre or style, target_duration if target_duration is not None else duration, character_anchor, "auto", None)

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
        return "v1-5-pruned-emaonly.safetensors"

    def generate_story(self, topic, style="Anime", duration=300, character_anchor="", provider="auto", status_callback=None, cache_dir=None):
        from story_writer import StoryWriter
        self._refresh_keys()
        return StoryWriter(self.keys, provider).write(topic, style, duration, character_anchor, status_callback, cache_dir)

    def generate_image(self, prompt, negative_prompt="", aspect_ratio="16:9", preferred_provider=None, privacy_mode=False, output_path=None, seed=None, reference=None):
        from comfy_client import ComfyClient
        import uuid
        sizes = {"16:9": (640, 384), "9:16": (384, 640), "1:1": (512, 512)}
        if aspect_ratio not in sizes:
            raise ValueError("Aspect ratio must be 16:9, 9:16, or 1:1.")
        if preferred_provider not in (None, "auto", "comfyui", "local", "local_privacy"):
            raise ValueError("Scene art currently uses local ComfyUI. Select the local provider.")
        target = Path(output_path) if output_path else self.output_dir / f"keyframe_{uuid.uuid4().hex}.png"
        width, height = sizes[aspect_ratio]
        checkpoint = self._get_available_checkpoint()
        image_path = ComfyClient(self.comfyui_base_url).image(prompt, negative_prompt or "blurry, low quality, watermark, text, bad anatomy", checkpoint, target, width, height, seed, reference=reference)
        with Image.open(image_path) as image:
            image.verify()
        return {"success": True, "provider": "local_privacy" if privacy_mode else "comfyui", "image_path": image_path, "prompt": prompt}

    def refine_shot(self, shot_id, original_prompt, tweak_instruction, topic="", genre="Anime"):
        from story_writer import StoryWriter
        from prompt_guard import PromptGuard
        guard = PromptGuard()
        guard.require_config()
        self._refresh_keys()
        result = StoryWriter(self.keys).request(f"Refine this anime shot without losing character identity. Topic: {topic}. Style: {genre}. Original shot: {original_prompt}. Requested change: {tweak_instruction}. Return {{\"prompt\":\"refined visual prompt\",\"framing\":\"camera framing\"}}.", 1000)
        if not isinstance(result.get("prompt"), str) or not result["prompt"].strip():
            raise RuntimeError("Writer returned an empty refined shot.")
        guard.approve({"original": original_prompt, "candidate": result, "requested_change": tweak_instruction}, {"identity": "Does this refinement preserve all original character identity, costume, accessories and scene continuity without introducing contradictions?"})
        return dict(result, success=True, shotId=shot_id)

    def generate_motion(self, prompt, style, aspect_ratio, output_path):
        from comfy_client import ComfyClient
        import uuid
        client = ComfyClient(self.comfyui_base_url)
        available = client.info("ADE_AnimateDiffLoaderWithContext")["input"]["required"]["model_name"][0]
        model = next((m for m in ("animatediff_lightning_4step_comfyui.safetensors", "mm_sd_v15_v2.ckpt") if m in available), None)
        if model is None:
            raise RuntimeError("Install an SD 1.5 AnimateDiff motion model to use motion clips.")
        client.info("VHS_VideoCombine")
        positive, negative = expand_prompt_with_style(prompt, style)
        width, height = {"16:9": (512, 320), "9:16": (320, 512), "1:1": (512, 512)}[aspect_ratio]
        graph = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": self._get_available_checkpoint()}},
            "2": {"class_type": "ADE_AnimateDiffLoaderWithContext", "inputs": {"model": ["1", 0], "model_name": model, "beta_schedule": "autoselect"}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["1", 1]}},
            "4": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 1]}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 16}},
            "6": {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": ["3", 0], "negative": ["4", 0], "latent_image": ["5", 0], "seed": uuid.uuid4().int % (2**63), "steps": 4 if "lightning" in model else 15, "cfg": 1.5 if "lightning" in model else 7.0, "sampler_name": "euler", "scheduler": "sgm_uniform" if "lightning" in model else "normal", "denoise": 1.0}},
            "7": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["6", 0], "vae": ["1", 2], "tile_size": 256, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}},
            "8": {"class_type": "VHS_VideoCombine", "inputs": {"images": ["7", 0], "frame_rate": 8.0, "loop_count": 0, "filename_prefix": f"ode/{uuid.uuid4().hex}", "format": "video/h264-mp4", "pingpong": False, "save_output": True, "pix_fmt": "yuv420p", "crf": 19, "save_metadata": True}},
        }
        return client.render(graph, output_path, ".mp4")


if __name__ == "__main__":
    router = OmniRouter()
    print("Provider Status:", json.dumps(router.get_provider_status(), indent=2))
    print(f"Total Available Styles: {len(STYLE_PRESETS)}")
    print("Testing OpenRouter Free Script Generation...")
    sample_script = router.generate_script("Cyberpunk cat on a neon rooftop", genre="Cyberpunk 2077", target_duration=15)
    print("Generated Script Result:", json.dumps(sample_script, indent=2))
