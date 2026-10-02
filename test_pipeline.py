import json
from omnirouter import OmniRouter

router = OmniRouter()

print("\n--- GENERATING 30-SECOND SCRIPT & KEYFRAMES ---")
topic = "A young boy happily playing fetch and running with his energetic golden retriever dog in a sunny green park"
script = router.generate_script(topic, genre="2D Cartoon Animation", target_duration=30)

success_flag = script.get("success", False)
shots = script.get("shots", [])
print(f"Script Success: {success_flag} | Shots Generated: {len(shots)}")

print("\n--- BATCH GENERATING ALL KEYFRAMES VIA LOCAL COMFYUI ---")
for shot in shots:
    title = shot.get("title", "Shot")
    prompt = shot.get("prompt", topic)
    print(f"-> Rendering {title}...")
    res = router.generate_image(prompt, aspect_ratio="16:9")
    print(json.dumps(res, indent=2))

print("\n--- GENERATION COMPLETE ---")
