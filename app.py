import json
import time
from pathlib import Path
import gradio as gr
from omnirouter import OmniRouter

# Initialize OmniRouter pipeline
router = OmniRouter()


def get_server_status_markdown():
    """Returns formatted Markdown status for the top health bar."""
    status = router.get_provider_status()
    comfy_info = status.get("comfyui", {})
    comfy_online = comfy_info.get("configured", False)
    
    if comfy_online:
        return (
            "🟢 **Local ComfyUI Backend:** Online & Ready (`http://127.0.0.1:8188`) | "
            "**GPU Acceleration:** Enabled (NVIDIA GTX 1660 SUPER)"
        )
    return (
        "🔴 **Local ComfyUI Backend:** Offline | "
        "*Ensure `python main.py --listen 127.0.0.1 --port 8188` is running in your ComfyUI terminal.*"
    )


def run_production_pipeline(topic, genre, duration, aspect_ratio, progress=gr.Progress()):
    """Executes the full pipeline: script generation -> ComfyUI batch rendering -> UI updates."""
    if not topic.strip():
        return "⚠️ **Error:** Please enter a prompt or story topic to begin.", [], ""

    # Phase 1: Script & Shot List Generation
    progress(0.05, desc="✨ Step 1/3: Generating AI Animation Script & Shot List...")
    script_res = router.generate_script(topic=topic, genre=genre, target_duration=duration)
    
    if not script_res.get("success"):
        return f"❌ Script generation failed: {script_res}", [], ""

    shots = script_res.get("shots", [])
    script_text = script_res.get("scriptText", f"Scene: {topic}")
    
    # Format readable script output
    formatted_script = f"### 🎬 Scene Script\n{script_text}\n\n"
    formatted_script += f"### 🎥 Shot Breakdown ({len(shots)} Total Shots)\n"
    for shot in shots:
        formatted_script += (
            f"- **{shot.get('title', 'Shot')}** "
            f"*(Framing: {shot.get('framing', 'Wide')}, Duration: {shot.get('duration', 5)}s)*: "
            f"{shot.get('prompt')}\n"
        )

    # Phase 2: Batch Render Keyframes via ComfyUI
    total_shots = len(shots)
    progress(0.20, desc=f"🎨 Step 2/3: Prepared {total_shots} shots. Starting local ComfyUI batch render...")
    
    rendered_gallery = []

    for idx, shot in enumerate(shots):
        # Calculate granular progress (20% to 95%)
        pct = 0.20 + (0.75 * ((idx + 1) / total_shots))
        shot_title = shot.get("title", f"Shot {idx+1}")
        shot_prompt = shot.get("prompt", topic)
        
        progress(pct, desc=f"⏳ Step 3/3: Rendering {shot_title} ({idx+1}/{total_shots}) via GTX 1660 SUPER...")
        
        # Trigger image generation through OmniRouter
        img_res = router.generate_image(prompt=shot_prompt, aspect_ratio=aspect_ratio)
        
        if img_res.get("success"):
            img_path = img_res.get("image_path")
            provider = img_res.get("provider", "comfyui")
            caption = f"{shot_title} [{provider.upper()}] | {shot.get('framing', '')}"
            rendered_gallery.append((img_path, caption))

    progress(1.0, desc="🎉 Production Complete! All keyframes rendered.")
    
    return formatted_script, rendered_gallery, json.dumps(script_res, indent=2)


# =============================================================================
# GRADIO UI DASHBOARD
# =============================================================================

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate",
)

custom_css = """
#status-banner {
    padding: 12px 16px;
    border-radius: 8px;
    background-color: #1e293b;
    border: 1px solid #334155;
    margin-bottom: 12px;
}
#generate-btn {
    font-size: 16px;
    font-weight: 600;
}
"""

with gr.Blocks(title="Open Drama Engine v2.0", theme=theme, css=custom_css) as demo:
    gr.Markdown("# 🎬 Open Drama Engine v2.0")
    gr.Markdown("Automated 2D Animation Scripting & Local ComfyUI Keyframe Generation Studio")

    # Top Status Bar
    with gr.Row(elem_id="status-banner"):
        status_markdown = gr.Markdown(value=get_server_status_markdown())
        refresh_btn = gr.Button("🔄 Refresh Status", size="sm", scale=0)

    # Main Interface Split
    with gr.Row():
        # Left Panel: Production Controls
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Production Controls")
            
            topic_input = gr.Textbox(
                label="Prompt / Story Topic",
                placeholder="A boy playing fetch with his golden retriever dog in a sunny green park",
                lines=3,
                value="A young boy happily playing fetch and running with his energetic golden retriever in a sunny park"
            )
            
            genre_input = gr.Dropdown(
                label="Animation Style",
                choices=[
                    "2D Cartoon Animation",
                    "2D Cyberpunk Anime",
                    "Vibrant Cell-Shaded",
                    "Cinematic Fantasy"
                ],
                value="2D Cartoon Animation"
            )
            
            duration_input = gr.Slider(
                label="Target Scene Duration (Seconds)",
                minimum=10,
                maximum=60,
                step=5,
                value=30
            )
            
            aspect_ratio_input = gr.Radio(
                label="Aspect Ratio",
                choices=["16:9", "9:16", "1:1"],
                value="16:9"
            )
            
            generate_btn = gr.Button("🚀 Generate Script & Keyframes", variant="primary", size="lg", elem_id="generate-btn")

        # Right Panel: Output Gallery & Script View
        with gr.Column(scale=2):
            gr.Markdown("### 🎨 Rendered Keyframe Gallery")
            
            gallery_output = gr.Gallery(
                label="Generated Keyframes",
                columns=2,
                rows=2,
                height="auto",
                object_fit="contain",
                preview=True
            )
            
            with gr.Accordion("📜 Generated Scene Script & Shot List", open=True):
                script_output = gr.Markdown(value="*Click 'Generate Script & Keyframes' to start production.*")

            with gr.Accordion("🔍 Raw JSON Metadata", open=False):
                json_output = gr.Code(language="json")

    # Event Bindings
    refresh_btn.click(
        fn=get_server_status_markdown,
        outputs=status_markdown
    )
    
    generate_btn.click(
        fn=run_production_pipeline,
        inputs=[topic_input, genre_input, duration_input, aspect_ratio_input],
        outputs=[script_output, gallery_output, json_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
