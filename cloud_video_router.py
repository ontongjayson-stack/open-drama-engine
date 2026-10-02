import os
import sys
import time
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from gradio_client import Client
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False

from assemble_clips import is_valid_mp4

logging.basicConfig(level=logging.INFO, format="[CloudVideo] %(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CloudVideo")

DEFAULT_HF_SPACE = "Lightricks/ltx-video-distilled"
FALLBACK_HF_SPACE = "mediasynthesismuseum/modelscope-text-to-video"

class CloudVideoRouter:
    """
    Zero-VRAM Cloud Video Diffusion Engine:
    - Primary: Lightricks/ltx-video-distilled (704x512, 30 FPS, True Fluid Motion Video).
    - Fallback: mediasynthesismuseum/modelscope-text-to-video.
    - Custom: Remote Colab / Cloudflare Tunnel URL (Wan 2.1, AnimateDiff, LTX).
    """

    def __init__(self, hf_token=None, custom_remote_url=None):
        self.hf_token = hf_token or os.getenv("HUGGINGFACE_API_KEY")
        self.custom_remote_url = custom_remote_url or os.getenv("REMOTE_VIDEO_API_URL")
        self._client_cache = {}

    def is_available(self):
        return GRADIO_AVAILABLE

    def _get_client(self, target_endpoint):
        if target_endpoint in self._client_cache:
            return self._client_cache[target_endpoint]

        token = self.hf_token if ("hf.space" in target_endpoint or "/" in target_endpoint) else None
        try:
            logger.info(f"Connecting to Gradio endpoint: {target_endpoint} (authenticated: {bool(token)})")
            client = Client(target_endpoint, token=token)
            self._client_cache[target_endpoint] = client
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Gradio endpoint {target_endpoint}: {e}")
            return None

    def _render_discovered(self, client, prompt, endpoints, status_callback=None):
        """Use the endpoint's advertised parameters instead of a fixed positional payload."""
        info = client.view_api(print_info=False, return_format="dict")
        available = info.get("named_endpoints", {})
        endpoint = next((name for name in endpoints if name in available), None)
        if not endpoint:
            raise RuntimeError(f"Compatible text-to-video endpoint missing. Available: {list(available)}")
        values = {}
        has_prompt = False
        for parameter in available[endpoint].get("parameters", []):
            name = parameter.get("parameter_name") or parameter.get("label", "")
            if name in ("prompt", "text", "positive_prompt"):
                values[name] = prompt
                has_prompt = True
            elif parameter.get("parameter_has_default"):
                values[name] = parameter.get("parameter_default")
            elif name in ("negative_prompt", "negative"):
                values[name] = "blurry, distorted, jittery, watermark, text"
            elif name in ("seed", "random_seed"):
                values[name] = 42
            else:
                raise RuntimeError(f"Video endpoint requires unsupported parameter '{name}'. Configure a compatible text-to-video Gradio endpoint.")
        if not has_prompt:
            raise RuntimeError("Video endpoint does not advertise a text prompt parameter.")
        job = client.submit(api_name=endpoint, **values)
        start = time.monotonic()
        while not job.done():
            if time.monotonic() - start > 300:
                try:
                    job.cancel()
                except Exception:
                    pass
                raise TimeoutError("Cloud video generation exceeded five minutes.")
            if status_callback:
                status_callback(f"Cloud video rendering... {int(time.monotonic() - start)}s elapsed")
            time.sleep(2)
        def find_file(value):
            if isinstance(value, str) and value.lower().endswith(".mp4") and Path(value).is_file():
                return value
            if isinstance(value, dict):
                for name in ("video", "path", "name"):
                    found = find_file(value.get(name))
                    if found:
                        return found
            if isinstance(value, (tuple, list)):
                for item in value:
                    found = find_file(item)
                    if found:
                        return found
            return None
        video = find_file(job.result())
        if not video:
            raise RuntimeError("Cloud endpoint returned no downloaded MP4 video.")
        return video

    def _render_ltx(self, client, prompt, status_callback=None, max_retries=2):
        return self._render_discovered(client, prompt, ["/text_to_video", "/generate_video", "/generate"], status_callback)

    def _render_modelscope(self, client, prompt, status_callback=None, max_retries=2):
        return self._render_discovered(client, prompt, ["/generate", "/text_to_video"], status_callback)

    def render_scene(self, prompt: str, output_path: Path, backend_target="cloud", custom_url=None, status_callback=None) -> bool:
        """
        Renders a single scene prompt into a playable MP4 video file.
        Passes raw generated video directly to output_path without text overlays.
        Returns True on success, False otherwise.
        """
        if not GRADIO_AVAILABLE:
            err = "gradio_client package not installed."
            logger.error(err)
            if status_callback:
                status_callback(f"Error: {err}")
            return False

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Custom URL Handling
        if backend_target == "custom" and (custom_url or self.custom_remote_url):
            target = custom_url or self.custom_remote_url
            if status_callback:
                status_callback(f"Connecting to custom video endpoint ({target})...")
            client = self._get_client(target)
            if not client:
                err = f"Could not connect to custom video backend: {target}"
                logger.error(err)
                if status_callback:
                    status_callback(f"Error: {err}")
                return False

            try:
                raw_video_path = self._render_ltx(client, prompt, status_callback)
                shutil.copy2(raw_video_path, str(output_path))
                if output_path.exists() and output_path.stat().st_size > 1024 and is_valid_mp4(str(output_path)):
                    logger.info(f"✅ Scene successfully rendered via custom endpoint: {output_path}")
                    return True
            except Exception as e:
                logger.error(f"Custom endpoint render failed: {e}")
                if status_callback:
                    status_callback(f"Custom endpoint error: {e}")
                return False

        # 2. Cloud Primary (Lightricks/ltx-video-distilled - True 30fps Video)
        client_primary = self._get_client(DEFAULT_HF_SPACE)
        if client_primary:
            if status_callback:
                status_callback("Connecting to primary cloud engine (LTX-Video 30fps)...")
            try:
                raw_video_path = self._render_ltx(client_primary, prompt, status_callback)
                if raw_video_path and os.path.exists(raw_video_path):
                    shutil.copy2(raw_video_path, str(output_path))
                    if output_path.exists() and output_path.stat().st_size > 1024 and is_valid_mp4(str(output_path)):
                        logger.info(f"✅ Scene successfully rendered via LTX-Video: {output_path} ({output_path.stat().st_size} bytes)")
                        if status_callback:
                            status_callback("Scene video rendered (30fps fluid motion)!")
                        return True
            except Exception as e:
                logger.warning(f"Primary LTX-Video diffusion failed: {e}. Trying fallback engine...")
                if status_callback:
                    status_callback("Primary engine busy. Falling back to ModelScope...")

        # 3. Cloud Fallback (mediasynthesismuseum/modelscope-text-to-video)
        client_fallback = self._get_client(FALLBACK_HF_SPACE)
        if client_fallback:
            try:
                raw_video_path = self._render_modelscope(client_fallback, prompt, status_callback)
                if raw_video_path and os.path.exists(raw_video_path):
                    shutil.copy2(raw_video_path, str(output_path))
                    if output_path.exists() and output_path.stat().st_size > 1024 and is_valid_mp4(str(output_path)):
                        logger.info(f"✅ Scene successfully rendered via fallback ModelScope: {output_path} ({output_path.stat().st_size} bytes)")
                        if status_callback:
                            status_callback("Scene video rendered via fallback!")
                        return True
            except Exception as e:
                logger.error(f"Fallback ModelScope diffusion failed: {e}", exc_info=True)
                if status_callback:
                    status_callback(f"Cloud render error: {str(e)}")

        return False


if __name__ == "__main__":
    router = CloudVideoRouter()
    print("Gradio Client Available:", router.is_available())
    test_out = Path("generated_assets/test_ltx_scene.mp4")
    success = router.render_scene("A cute little blue robot smiling in a sunny garden", test_out, status_callback=print)
    print("Render Success:", success)
    if success:
        print("File size:", test_out.stat().st_size)
