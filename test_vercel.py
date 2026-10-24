"""Smoke tests for the read-only, web-only Vercel deployment."""
import importlib.util
import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parent


def test_vercel_uses_one_fastapi_entrypoint():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert config["framework"] == "fastapi"
    assert "services" not in config
    assert "rewrites" not in config
    assert (ROOT / "app.py").exists()

    function = config["functions"]["app.py"]
    for asset in ("templates/**", "static/**", "ode_icon.ico"):
        assert asset in function["includeFiles"]
    excluded = function["excludeFiles"].strip("{}").split(",")
    assert "index.html" not in excluded
    assert "setup_env.py" in excluded


def test_vercel_ignore_preserves_the_dashboard_template():
    """The Vercel upload ignore file uses Git-style filename matching."""
    command = ["git", "-c", f"core.excludesfile={ROOT / '.vercelignore'}", "check-ignore", "--no-index", "-v"]
    required = ["app.py", "requirements.txt", "templates/index.html", "static/obsidian-studio.css", "static/manifest.json", "static/icons/icon-192.png", "ode_icon.ico"]
    result = subprocess.run(command + required, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 1, result.stdout + result.stderr

    # The old frontend entrypoint at the repository root must still be excluded.
    root_index = subprocess.run(command + ["index.html"], cwd=ROOT, capture_output=True, text=True)
    assert root_index.returncode == 0, root_index.stderr
    assert ".vercelignore" in root_index.stdout

    # The real credentials file and its setup helper must not ship to Vercel.
    ignore_lines = (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in ignore_lines
    assert ".env.*" in ignore_lines
    ignored = subprocess.run(command + [".env", "setup_env.py"], cwd=ROOT, capture_output=True, text=True)
    assert ignored.returncode == 0, ignored.stdout + ignored.stderr


def test_hosted_dashboard_works_without_writing_to_source_or_starting_jobs(monkeypatch):
    original_mkdir = Path.mkdir

    def refuse_source_writes(directory, *args, **kwargs):
        if directory.is_relative_to(ROOT):
            raise AssertionError(f"Vercel cannot write to the source tree: {directory}")
        return original_mkdir(directory, *args, **kwargs)

    # Import the entrypoint as Vercel would, with a read-only project tree.
    with monkeypatch.context() as patch:
        patch.setenv("VERCEL", "1")
        patch.setattr(Path, "mkdir", refuse_source_writes)
        spec = importlib.util.spec_from_file_location("vercel_app_smoke_test", ROOT / "app.py")
        hosted = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hosted)

    assert hosted.IS_VERCEL
    assert not hosted.ASSETS_DIR.is_relative_to(ROOT)
    assert not any(getattr(route, "path", "") == "/generated_assets" for route in hosted.app.routes)

    # A public status request must not try to contact the caller's localhost.
    def fail_local_probe():
        raise AssertionError("hosted status tried to contact the local GPU")

    monkeypatch.setattr(hosted, "check_comfy_status", fail_local_probe)
    monkeypatch.setattr(hosted.router, "_check_comfyui_online", fail_local_probe)
    with TestClient(hosted.app) as client:
        dashboard = client.get("/")
        assert dashboard.status_code == 200
        assert "hosted-notice" in dashboard.text
        assert client.get("/static/obsidian-studio.css").status_code == 200
        assert client.get("/static/icons/icon-192.png").status_code == 200
        assert client.get("/manifest.json").status_code == 200
        assert client.get("/sw.js").status_code == 200
        assert client.get("/favicon.ico").status_code == 200
        assert len(client.get("/api/styles").json()["styles"]) == 15

        status = client.get("/api/status")
        assert status.status_code == 200
        assert status.json()["runtime"] == "vercel"
        assert status.json()["production_available"] is False
        assert status.json()["comfyui_online"] is False
        assert status.json()["continuity_review_enabled"] is False
        assert status.json()["providers"]["comfyui"]["configured"] is False
        assert "local" in status.json()["production_message"].lower()

        for method, path, kwargs in [
            ("post", "/api/generate", {"json": {"prompt": "A guardian rescues a village"}}),
            ("post", "/api/start-comfy", {}),
            ("get", "/api/jobs/123456abcdef", {}),
            ("post", "/api/jobs/123456abcdef/resume", {}),
            ("get", "/api/stream/123456abcdef", {}),
            ("post", "/api/install-desktop", {}),
        ]:
            response = getattr(client, method)(path, **kwargs)
            assert response.status_code == 503, (path, response.text)
            assert "Vercel" in response.json()["detail"]


def test_local_status_and_generated_assets_are_unchanged(monkeypatch):
    import app as studio

    assert not studio.IS_VERCEL
    monkeypatch.setattr(studio, "check_comfy_status", lambda: -1)
    monkeypatch.setattr(studio.router, "_check_comfyui_online", lambda: False)
    with TestClient(studio.app) as client:
        status = client.get("/api/status").json()
        assert status["runtime"] == "local"
        assert status["production_available"] is True
        assert status["continuity_review_enabled"] is True
        assert status["comfyui_online"] is False
        assert client.get("/static/obsidian-studio.css").status_code == 200
    assert any(getattr(route, "path", "") == "/generated_assets" for route in studio.app.routes)
