# ?? Open Drama Engine v2.0

Open Drama Engine is an open-source, automated 2D animation scripting and keyframe generation studio.

## ?? Key Features

* **Gradio Web Dashboard (\pp.py\):** Clean browser interface for prompt input, script view, and live rendering progress.
* **Local ComfyUI Pipeline:** Zero-cost local image generation powered by GPU acceleration.
* **Dynamic Checkpoint Discovery:** Automatically detects installed model checkpoints (\DreamShaper_8_pruned.safetensors\, \1-5-pruned-emaonly.safetensors\).
* **Multi-Provider Scripting:** Interfaces with Gemini API and local LLM fallbacks for multi-shot scene scripting.

---

## ??? Quick Start

### 1. Launch ComfyUI Server
\\\powershell
cd D:\AI DEVELOPMENTS\ComfyUI
.\venv\Scripts\activate
python main.py --listen 127.0.0.1 --port 8188
\\\`n
### 2. Launch Open Drama Engine Web UI
\\\powershell
cd D:\AI DEVELOPMENTS\OPEN-DRAMA-ENGINE
python app.py
\\\`nOpen \http://127.0.0.1:7860\ in your web browser.
