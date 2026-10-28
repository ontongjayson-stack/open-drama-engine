"""Create the real, private local .env without overwriting existing credentials.

Run ``python setup_env.py`` from any directory. Deployment environment variables
belong in the Vercel project's settings, never in this repository.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def create_env(root: Path = ROOT) -> bool:
    """Copy .env.example to .env exactly once; return whether it was created."""
    template = (root / ".env.example").read_bytes()
    destination = root / ".env"
    try:
        # Exclusive creation prevents accidentally truncating a user's secrets,
        # even if two setup commands are run at the same time.
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False

    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(template)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return True


def main() -> int:
    try:
        created = create_env()
    except OSError as exc:
        print(f"Could not set up .env: {exc}", file=sys.stderr)
        return 1

    if created:
        print("Created private .env. Edit GEMINI_API_KEY or OPENROUTER_API_KEY to render locally.")
    else:
        print(".env already exists; kept your settings unchanged.")
    print(".env is ignored by Git and Vercel. Vercel preview cannot render films.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
