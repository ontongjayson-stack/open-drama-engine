import os
import sys
import time
import json
import shutil
import glob
import re
import uuid
import asyncio
import logging
import threading
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from story_production import StoryProduction
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from omnirouter import OmniRouter, expand_prompt_with_style, get_available_styles, STYLE_PRESETS
from cloud_video_router import CloudVideoRouter

logging.basicConfig(level=logging.INFO, format="[AppServer] %(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AppServer")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "generated_assets"
STATIC_DIR = BASE_DIR / "static"
COMFY_OUTPUT_DIR = Path(r"D:\AI DEVELOPMENTS\ComfyUI\output")
COMFY_URL = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188").rstrip("/")

# Ensure directories exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Open Drama Engine — AI Studio Pro", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset folders
app.mount("/generated_assets", StaticFiles(directory=str(ASSETS_DIR)), name="generated_assets")
if TEMPLATES_DIR.exists():
    app.mount("/templates", StaticFiles(directory=str(TEMPLATES_DIR)), name="templates")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

router = OmniRouter(workspace_dir=str(BASE_DIR))
cloud_video = CloudVideoRouter()

# In-memory store for real-time progress streaming
job_states = {}
job_queues = {}
job_locks = threading.Lock()
production_lock = threading.Lock()


def check_comfy_status():
    """Returns total active/pending jobs in ComfyUI queue or -1 if unreachable."""
    try:
        req = urllib.request.Request(f"{COMFY_URL}/queue")
        with urllib.request.urlopen(req, timeout=3) as response:
            queue_data = json.loads(response.read().decode("utf-8"))
            exec_info = queue_data.get("queue_running", []) + queue_data.get("queue_pending", [])
            return len(exec_info)
    except Exception:
        return -1


def ensure_comfy_running(timeout=35, job_id=None):
    """Checks if ComfyUI is running; if not, launches it in the background with fp32 VAE and waits until active."""
    if check_comfy_status() != -1:
        return True

    if COMFY_URL not in ("http://127.0.0.1:8188", "http://localhost:8188"):
        return False

    logger.info("[Director] Booting Local ComfyUI GPU Render Engine in background...")
    if job_id:
        emit_event(job_id, {
            "percent": 63,
            "status_text": "Booting Local ComfyUI GPU Engine in background...",
            "active_agent": "director",
            "agent_activity": "Starting ComfyUI server...",
            "completed_agents": ["brain", "writer", "artist"],
            "log": "[Director] Booting Local ComfyUI GPU Engine in background (127.0.0.1:8188)...",
            "log_type": "info"
        })

    comfy_dir = Path(os.getenv("COMFYUI_DIR", r"D:\AI DEVELOPMENTS\ComfyUI"))
    python_exe = comfy_dir / "venv" / "Scripts" / "python.exe"
    main_py = comfy_dir / "main.py"
    if python_exe.exists() and main_py.exists():
        cmd = [
            str(python_exe),
            str(main_py),
            "--listen", "127.0.0.1",
            "--port", "8188",
            "--fp32-vae",
            "--lowvram",
            "--preview-method", "auto"
        ]
        with open(BASE_DIR / "comfy_engine.log", "a", encoding="utf-8") as engine_log:
            subprocess.Popen(
                cmd,
                cwd=str(comfy_dir),
                stdout=engine_log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
    else:
        comfy_bat = comfy_dir / "start_comfy.bat"
        if comfy_bat.exists():
            subprocess.Popen(
                ["cmd.exe", "/c", str(comfy_bat)],
                cwd=str(comfy_dir),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        if check_comfy_status() != -1:
            logger.info("✅ [Director] ComfyUI GPU Render Engine is now active and ready!")
            return True

    return check_comfy_status() != -1


def emit_event(job_id, payload):
    """Publish from the worker on each subscriber's own asyncio event loop."""
    with job_locks:
        current = dict(job_states.get(job_id, {}))
        current.update(payload)
        job_states[job_id] = current
        subscribers = list(job_queues.get(job_id, []))
    root = ASSETS_DIR / "jobs" / job_id
    if root.exists():
        temporary = root / "status.tmp"
        temporary.write_text(json.dumps(current, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, root / "status.json")
    for queue, loop in subscribers:
        if not loop.is_closed():
            loop.call_soon_threadsafe(queue.put_nowait, payload)


def run_orchestration_job(job_id, settings):
    try:
        emit_event(job_id, {"percent": 3, "status_text": "Checking production engines...", "active_agent": "brain"})
        if settings["production_mode"] == "story" or settings["video_backend"] in ("local", "auto"):
            if not ensure_comfy_running(timeout=120):
                raise RuntimeError(f"ComfyUI could not start at {COMFY_URL}. Check the engine log and configured installation path.")
        result = StoryProduction(BASE_DIR).run(job_id, callback=lambda event: emit_event(job_id, event), **settings)
        prefix = f"/generated_assets/jobs/{job_id}"
        emit_event(job_id, {"percent": 100, "status_text": f"Story ready: {result['scene_count']} scenes, {result['duration']:.1f}s, {result['resolution']}", "done": True, "error": False, "video_url": prefix + "/master_story.mp4", "script_url": prefix + "/script.txt", "subtitles_url": prefix + "/subtitles.srt", "result": result, "completed_agents": ["brain", "writer", "artist", "director", "voice", "composer"]})
    except Exception as exc:
        logger.exception("Story production failed for %s", job_id)
        emit_event(job_id, {"status_text": str(exc), "error": str(exc), "done": False, "log": str(exc), "log_type": "error"})
    finally:
        production_lock.release()


class ProductionRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=6000)
    style: str = "Anime"
    duration: int = Field(default=300, ge=12, le=1500)
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    resolution: Literal["Standard (512p)", "HD (720p)"] = "HD (720p)"
    include_subtitles: bool = True
    character_anchor: str = Field(default="", max_length=1500)
    engine_provider: Literal["auto", "gemini", "openrouter"] = "auto"
    video_backend: Literal["auto", "local", "cloud", "custom"] = "local"
    production_mode: Literal["story", "motion"] = "story"
    custom_video_url: str = ""

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value):
        value = value.strip()
        if len(value) < 5:
            raise ValueError("Please describe the story in at least five characters.")
        return value

    @field_validator("style")
    @classmethod
    def validate_style(cls, value):
        if value not in STYLE_PRESETS:
            raise ValueError("Select a supported visual style.")
        return value


def dispatch_production(job_id, settings):
    if not production_lock.acquire(blocking=False):
        raise HTTPException(409, "A story is already rendering. Wait for it to finish before starting another.")
    try:
        from prompt_guard import PromptGuard
        try:
            router._refresh_keys()
            PromptGuard().require_config()
            if not (router.keys.get("gemini") or router.keys.get("openrouter")):
                raise RuntimeError("An existing vision-capable generation account is required for visual character verification.")
        except RuntimeError as exc:
            raise HTTPException(503, str(exc))
        root = ASSETS_DIR / "jobs" / job_id
        root.mkdir(parents=True, exist_ok=True)
        (root / "request.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
        with job_locks:
            job_queues[job_id] = []
            job_states[job_id] = {"percent": 0, "status_text": "Starting story production", "done": False, "error": False}
        worker = threading.Thread(target=run_orchestration_job, args=(job_id, settings), daemon=True)
        worker.start()
    except Exception:
        production_lock.release()
        raise
    return {"status": "started", "job_id": job_id}


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the AI Studio Pro Dashboard."""
    index_path = TEMPLATES_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Error: templates/index.html not found.</h1>", status_code=404)


@app.get("/api/status")
async def get_system_status():
    """Returns server telemetry: ComfyUI, Gemini, OpenRouter, Cloud Video, and visual style presets."""
    comfy_online = (check_comfy_status() != -1)
    provider_info = router.get_provider_status()
    return {
        "status": "online",
        "comfyui_online": comfy_online,
        "cloud_video_available": cloud_video.is_available(),
        "continuity_review_enabled": True,
        "gemini_configured": provider_info.get("gemini", {}).get("configured", False),
        "openrouter_configured": provider_info.get("openrouter_free", {}).get("configured", False),
        "providers": provider_info,
        "total_styles": len(STYLE_PRESETS)
    }


@app.get("/api/styles")
async def get_styles():
    """Returns the list of 15 visual styles."""
    return {"styles": get_available_styles()}


@app.post("/api/start-comfy")
async def start_comfy_server():
    """Boots local ComfyUI GPU engine in background if not already active."""
    if check_comfy_status() != -1:
        return {"status": "already_running", "message": "ComfyUI is already active on http://127.0.0.1:8188"}

    comfy_bat = Path(r"D:\AI DEVELOPMENTS\ComfyUI\start_comfy.bat")
    if comfy_bat.exists():
        subprocess.Popen(
            ["cmd.exe", "/c", str(comfy_bat)],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return {"status": "starting", "message": "ComfyUI GPU engine is booting in the background..."}
    return JSONResponse({"status": "error", "message": "start_comfy.bat not found at D:\\AI DEVELOPMENTS\\ComfyUI"}, status_code=500)


@app.post("/api/generate")
async def start_generation(body: ProductionRequest):
    if body.production_mode == "motion":
        raise HTTPException(422, "Motion providers cannot yet enforce your identity and frame continuity requirements. Choose the checked illustrated story format.")
    return dispatch_production(uuid.uuid4().hex[:12], body.model_dump())


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if not re.fullmatch(r"[a-f0-9]{12}", job_id):
        raise HTTPException(404, "Story job not found.")
    with job_locks:
        if job_id in job_states:
            return job_states[job_id]
    saved = ASSETS_DIR / "jobs" / job_id / "status.json"
    if not saved.exists():
        raise HTTPException(404, "Story job not found.")
    state = json.loads(saved.read_text(encoding="utf-8"))
    if not state.get("done") and not state.get("error"):
        state["error"] = "Production was interrupted. Resume this job to reuse its completed scenes."
    return state


@app.post("/api/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    state = await get_job(job_id)
    if state.get("done"):
        raise HTTPException(409, "This story is already complete.")
    path = ASSETS_DIR / "jobs" / job_id / "request.json"
    settings = ProductionRequest.model_validate(json.loads(path.read_text(encoding="utf-8"))).model_dump()
    return dispatch_production(job_id, settings)


@app.get("/api/stream/{job_id}")
async def stream_job_progress(job_id: str, request: Request):
    initial_state = await get_job(job_id)
    queue = asyncio.Queue()
    subscriber = (queue, asyncio.get_running_loop())
    with job_locks:
        job_queues.setdefault(job_id, []).append(subscriber)
        queue.put_nowait(dict(job_states.get(job_id, initial_state)))
    async def event_generator():
        try:
            while not await request.is_disconnected():
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("done") or data.get("error"):
                    break
        finally:
            with job_locks:
                if subscriber in job_queues.get(job_id, []):
                    job_queues[job_id].remove(subscriber)
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/master_story.mp4")
async def get_master_video():
    """Direct stream route for master_story.mp4."""
    video_path = ASSETS_DIR / "master_story.mp4"
    if video_path.exists():
        return FileResponse(str(video_path), media_type="video/mp4")
    return JSONResponse({"error": "master_story.mp4 not yet created"}, status_code=404)


@app.get("/manifest.json")
async def get_manifest():
    """Returns the PWA Web App Manifest."""
    manifest_path = STATIC_DIR / "manifest.json"
    if manifest_path.exists():
        return FileResponse(str(manifest_path), media_type="application/manifest+json")
    return JSONResponse({"error": "manifest.json not found"}, status_code=404)


@app.get("/sw.js")
async def get_service_worker():
    """Returns the PWA Service Worker."""
    sw_path = STATIC_DIR / "sw.js"
    if sw_path.exists():
        return FileResponse(str(sw_path), media_type="application/javascript")
    return JSONResponse({"error": "sw.js not found"}, status_code=404)


@app.get("/favicon.ico")
async def get_favicon():
    """Returns the desktop application icon as favicon."""
    ico_path = BASE_DIR / "ode_icon.ico"
    if ico_path.exists():
        return FileResponse(str(ico_path), media_type="image/x-icon")
    return JSONResponse({"error": "favicon not found"}, status_code=404)


@app.post("/api/install-desktop")
async def api_install_desktop():
    """Installs or updates the Open Drama Engine standalone desktop application shortcut."""
    try:
        from install_desktop_app import install_desktop_shortcut
        success, path_or_err = install_desktop_shortcut()
        if success:
            return JSONResponse({
                "status": "success",
                "message": "Desktop app shortcut installed successfully!",
                "shortcut_path": path_or_err
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": f"Could not create desktop shortcut: {path_or_err}"
            }, status_code=500)
    except Exception as e:
        logger.error(f"Error creating desktop shortcut: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


if __name__ == "__main__":
    logger.info("Starting Open Drama Engine AI Studio Pro on http://127.0.0.1:7860 ...")
    uvicorn.run(app, host="127.0.0.1", port=7860, log_level="info")
