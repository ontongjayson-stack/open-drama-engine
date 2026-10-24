"""Tests for the private local environment setup command."""

import os
import stat
from pathlib import Path

from setup_env import create_env


ROOT = Path(__file__).resolve().parent


def test_setup_creates_real_env_without_secrets_or_overwriting(tmp_path):
    template = (ROOT / ".env.example").read_bytes()
    (tmp_path / ".env.example").write_bytes(template)

    assert create_env(tmp_path) is True
    env_file = tmp_path / ".env"
    assert env_file.read_bytes() == template
    assert b"GEMINI_API_KEY=\n" in template
    assert b"OPENROUTER_API_KEY=\n" in template
    if os.name == "posix":
        assert stat.S_IMODE(env_file.stat().st_mode) == 0o600

    env_file.write_text("GEMINI_API_KEY=private-key\n", encoding="utf-8")
    assert create_env(tmp_path) is False
    assert env_file.read_text(encoding="utf-8") == "GEMINI_API_KEY=private-key\n"


def test_setup_requires_a_template(tmp_path):
    try:
        create_env(tmp_path)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("The command should fail rather than create a blank .env")
    assert not (tmp_path / ".env").exists()
