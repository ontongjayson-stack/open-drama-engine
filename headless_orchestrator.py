"""Headless entry point for the same verified story pipeline as the dashboard."""
import json
import shutil
import uuid
from pathlib import Path

from story_production import StoryProduction


class HeadlessStudioOrchestrator:
    def __init__(self, workspace_dir=None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).resolve().parent
        self.production = StoryProduction(self.workspace_dir)

    def orchestrate_film(self, topic, genre="Anime", duration=300, fps=24, aspect_ratio="16:9", privacy_mode=False, output_path=None, character_anchor="", provider="auto"):
        if fps != 24:
            raise ValueError("Story exports use 24 FPS. Set fps=24.")
        if privacy_mode:
            raise ValueError("Story writing currently uses a cloud writer. Privacy mode cannot be guaranteed; generate local scene art with generate_image(privacy_mode=True) instead.")
        result = self.production.run(uuid.uuid4().hex[:12], topic, duration, genre, aspect_ratio, character_anchor=character_anchor, engine_provider=provider)
        if output_path:
            target = Path(output_path)
            if not target.is_absolute():
                target = self.workspace_dir / target
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(result["output_path"], target)
            result["output_path"] = str(target)
        return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--duration", type=int, default=300)
    args = parser.parse_args()
    print(json.dumps(HeadlessStudioOrchestrator().orchestrate_film(args.prompt, duration=args.duration)))
