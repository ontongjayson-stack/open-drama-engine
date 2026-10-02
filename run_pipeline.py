"""Example story CLI; uses the same pipeline as the dashboard."""
from headless_orchestrator import HeadlessStudioOrchestrator

if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="A young boy learns patience after dropping the apple he picked, and shares it with a hungry friend. End with both friends planting its seeds.")
    parser.add_argument("--duration", type=int, default=60)
    args = parser.parse_args()
    print(json.dumps(HeadlessStudioOrchestrator().orchestrate_film(args.prompt, duration=args.duration)))
