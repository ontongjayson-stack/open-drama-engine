"""ComfyUI API adapter. Download only outputs belonging to the submitted prompt."""
import os
import time
import uuid
from pathlib import Path

import requests


class ComfyClient:
    def __init__(self, base_url=None, timeout=None):
        self.base_url = (base_url or os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188")).rstrip("/")
        self.timeout = timeout or int(os.getenv("COMFY_RENDER_TIMEOUT", "1200"))

    def info(self, node):
        response = requests.get(f"{self.base_url}/object_info/{node}", timeout=15)
        response.raise_for_status()
        data = response.json()
        if node not in data:
            raise RuntimeError(f"ComfyUI node {node} is not installed or failed to load.")
        return data[node]

    def render(self, workflow, destination, extension, callback=None):
        response = requests.post(f"{self.base_url}/prompt", json={"prompt": workflow, "client_id": uuid.uuid4().hex}, timeout=30)
        if not response.ok:
            raise RuntimeError(f"ComfyUI rejected workflow (HTTP {response.status_code}): {response.text[:2000]}")
        submitted = response.json()
        if submitted.get("node_errors") or not submitted.get("prompt_id"):
            raise RuntimeError(f"ComfyUI rejected workflow: {submitted}")
        prompt_id = submitted["prompt_id"]
        deadline = time.monotonic() + self.timeout
        failures = 0
        while time.monotonic() < deadline:
            try:
                response = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=15)
                response.raise_for_status()
                history = response.json().get(prompt_id)
                failures = 0
            except requests.RequestException as exc:
                failures += 1
                if failures >= 5:
                    raise RuntimeError("ComfyUI disconnected during rendering.") from exc
                time.sleep(2)
                continue
            if history:
                status = history.get("status", {})
                if status.get("status_str") == "error":
                    raise RuntimeError(f"ComfyUI execution failed: {status.get('messages')}")
                if status.get("completed"):
                    for output in history.get("outputs", {}).values():
                        for key in ("images", "gifs", "videos"):
                            for item in output.get(key, []):
                                if item.get("filename", "").lower().endswith(extension):
                                    params = {k: item.get(k, "") for k in ("filename", "subfolder", "type")}
                                    params["type"] = params["type"] or "output"
                                    media = requests.get(f"{self.base_url}/view", params=params, timeout=120)
                                    media.raise_for_status()
                                    destination = Path(destination)
                                    destination.parent.mkdir(parents=True, exist_ok=True)
                                    if len(media.content) < 1024:
                                        raise RuntimeError("ComfyUI returned an empty media output.")
                                    destination.write_bytes(media.content)
                                    return str(destination)
                    raise RuntimeError(f"ComfyUI prompt {prompt_id} completed without a {extension} output.")
            if callback:
                callback("ComfyUI is rendering scene art...")
            time.sleep(3)
        raise TimeoutError(f"ComfyUI prompt {prompt_id} exceeded {self.timeout}s. Check its queue before retrying.")

    def image(self, positive, negative, checkpoint, destination, width=640, height=384, seed=None, reference=None):
        graph = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["1", 1]}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 1]}},
            "4": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
            "5": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0], "seed": seed if seed is not None else uuid.uuid4().int % (2**63), "steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}},
            "6": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["5", 0], "vae": ["1", 2], "tile_size": 256, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}},
            "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": f"ode/{uuid.uuid4().hex}"}},
        }
        if reference:
            with Path(reference).open("rb") as image:
                response = requests.post(f"{self.base_url}/upload/image", files={"image": (f"ode_{uuid.uuid4().hex}.png", image, "image/png")}, data={"type": "input", "overwrite": "false"}, timeout=30)
            response.raise_for_status()
            uploaded = response.json()
            name = "/".join(part for part in (uploaded.get("subfolder", ""), uploaded["name"]) if part)
            graph["4"] = {"class_type": "LoadImage", "inputs": {"image": name}}
            graph["9"] = {"class_type": "ImageScale", "inputs": {"image": ["4", 0], "upscale_method": "lanczos", "width": width, "height": height, "crop": "center"}}
            graph["10"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["9", 0], "vae": ["1", 2]}}
            graph["5"]["inputs"].update(latent_image=["10", 0], denoise=.35)
        return self.render(graph, destination, ".png")
