# 🎬 Open Drama Engine — MVP Project Board & Architecture Matrix

> **License**: 100% Free and Open Source under the **Apache 2.0 License**  
> **Core Focus**: 2D Cartoon Animation & Video Production NLE Suite  
> **Repository Path**: `d:\AI DEVELOPMENTS\OPEN-DRAMA-ENGINE`

---

## 🏛️ Architectural Overview & Generation Routing Pipeline

Open Drama Engine incorporates a dual-tier generation architecture designed to provide maximum performance, total data privacy, and zero downtime:

```
                  ┌───────────────────────────────────────────────────────────┐
                  │              OPEN DRAMA ENGINE NLE CLIENT                 │
                  └─────────────────────────────┬─────────────────────────────┘
                                                │
                                 ┌──────────────┴──────────────┐
                                 │ Privacy Mode Toggle Active? │
                                 └──────┬──────────────┬───────┘
                                        │              │
                                   NO (Default)     YES (Checked)
                                        │              │
                                        ▼              │
                  ┌───────────────────────────┐        │
                  │   CLOUD ENGINE (PRIMARY)   │        │
                  │ Hugging Face Inference API│        │
                  │    / ZeroGPU (Free Tier)  │        │
                  └─────────────┬─────────────┘        │
                                │                      │
                        Rate Limit / HTTP 429?         │
                                │                      │
                                ▼                      ▼
                  ┌───────────────────────────────────────────┐
                  │          LOCAL ENGINE (FALLBACK)          │
                  │        Wan2GP Local Gradio Worker         │
                  │       http://127.0.0.1:7860/run/predict   │
                  └─────────────────────┬─────────────────────┘
                                        │
                                        ▼
                  ┌───────────────────────────────────────────┐
                  │       GRADIO FILE PATH RESOLVER           │
                  │ Parses FileData & Streams /file= Route    │
                  └─────────────────────┬─────────────────────┘
                                        │
                                        ▼
                  ┌───────────────────────────────────────────┐
                  │        TIMELINE & PROGRAM MONITOR         │
                  │   Auto-Populates Assets Bin & Video 1     │
                  └───────────────────────────────────────────┘
```

### 1. Default Tier (Cloud Engine Priority)
- **Primary Route**: All default shot generation requests (`🎬 Generate Shot`) route through the free **Cloud Hugging Face Inference API / ZeroGPU Endpoints** (`black-forest-labs/FLUX.1-schnell`) using `omnirouter.py` and `engine.js`.
- **Automatic Fallback Chaining**: If the Hugging Face API hits HTTP 429 rate-limiting, quota exhaustion, or connection timeouts, `OmniRouter` logs a diagnostic warning and seamlessly routes the payload to secondary cloud providers or the local execution engine.

### 2. Privacy Mode (Run Locally)
- **Manual Control**: A header toggle switch (`🔒 LOCAL ENGINE: PRIVACY MODE`) allows users to force local execution at any time.
- **Offline & Private**: Bypasses all external cloud APIs and sends generation payloads directly to the local **Wan2GP Gradio Backend** at `http://127.0.0.1:7860/run/predict` for 100% data privacy and offline rendering.

### 3. Local Media Streaming & Gradio File Resolution
- **Gradio FileData Output Parser**: `resolveGradioVideoUrl()` parses Gradio response objects (`data[0].url`, `data[0].path`, `data[0].name`) and string paths.
- **`http://127.0.0.1:7860/file=` Route**: Normalizes local video file paths and streams them over HTTP with proper `Content-Type: video/mp4` and `Access-Control-Allow-Origin: *` headers, ensuring 100% blank-free playback across the timeline and monitor preview.

---

## 🗂️ MVP Project Board Milestone Cards

### 📍 Milestone 1: Generation Pipeline & Route Verification

#### 🎴 Card 1: Cloud Hugging Face Inference API Verification
- **Status**: `COMPLETED & VERIFIED`
- **Description**: Route primary generation requests to free Cloud Hugging Face Inference API / ZeroGPU endpoints using `omnirouter.py` and free User Access Tokens (`hf_...`).
- **Acceptance Criteria**:
  - [x] Default shot generation initializes cloud HF inference.
  - [x] Stream and blob image/video data are parsed directly into assets library.
  - [x] Ken Burns motion sequence preview compiles automatically.

#### 🎴 Card 2: Privacy Mode & Local Fallback Execution
- **Status**: `COMPLETED & VERIFIED`
- **Description**: Add manual UI header toggle (`🔒 LOCAL ENGINE: PRIVACY MODE`) and automatic HTTP 429 rate-limit fallback to local Wan2GP worker (`http://127.0.0.1:7860/run/predict`).
- **Acceptance Criteria**:
  - [x] Toggling Privacy Mode updates status pill to `🔒 LOCAL ENGINE: PRIVACY MODE`.
  - [x] Payload bypasses cloud endpoints when Privacy Mode is checked.
  - [x] Automatic HTTP 429 rate-limit trigger routes to local engine smoothly.

#### 🎴 Card 3: Gradio Local File Resolution (`/file=`)
- **Status**: `COMPLETED & VERIFIED`
- **Description**: Implement Gradio FileData object output parsing and streaming over `http://127.0.0.1:7860/file=` route to ensure blank-free video element playback.
- **Acceptance Criteria**:
  - [x] `resolveGradioVideoUrl()` resolves object `{ url, path, name }` and string paths.
  - [x] `server.js` serves `/file=` streaming route with CORS and correct mime-types (`video/mp4`).
  - [x] Video player includes `onerror` console logger fallback.

---

### 📍 Milestone 2: Multitrack NLE Timeline & CapCut Editing Workflow

#### 🎴 Card 4: Piano Black Decluttered NLE Studio Layout
- **Status**: `COMPLETED & VERIFIED`
- **Description**: CapCut Web inspired studio layout with far-left icon rail (`Media`, `Prompts`, `Captions`, `Audio`, `Effects`, `Plugins`), piano black dropdown menu overrides (`#121316`), and 3-way resizable splitters.

#### 🎴 Card 5: NLE Time-Scale Zoom & 1-Second Ruler Ticks
- **Status**: `COMPLETED & VERIFIED`
- **Description**: True pixels-per-second (`pps`) scale zoom (18px/sec to 200px/sec), dynamic 1-second ruler tick marks, un-distorted typography inside clip blocks, Blade tool (`B`/`V`), snapping, and clip context menus (Split, Copy, Duplicate, Delete).

---

### 📍 Milestone 3: Librosa Beat-Synced Ken Burns MoviePy Render Engine

#### 🎴 Card 6: Multi-Provider API Router (`omnirouter.py`)
- **Status**: `COMPLETED & VERIFIED`
- **Description**: Multi-provider API router supporting Hugging Face, OpenRouter, Together AI, and PIL synthetic keyframe generation guard.

#### 🎴 Card 7: Beat-Synced Ken Burns Video Engine (`render_engine.py`)
- **Status**: `COMPLETED & VERIFIED`
- **Description**: Librosa audio beat detection, frame-by-frame Ken Burns zoom/pan camera movements, radial vignette, film grain, 2.39:1 letterboxing, text metadata overlays, and MP4 sequence export.

---

### 📍 Milestone 4: Self-Contained Desktop Application & Local Engine Manager

#### 🎴 Card 8: One-Click Desktop Host (`main.js` & `server.js`)
- **Status**: `COMPLETED & VERIFIED`
- **Description**: Electron main host process (`main.js`) silently spawning Node backend worker process (`server.js`) on `http://127.0.0.1:7860` with clean quit listeners.

#### 🎴 Card 9: First-Run Setup & Model Downloader Wizard
- **Status**: `COMPLETED & VERIFIED`
- **Description**: First-run setup modal for downloading Wan2GP 14B VAE weights (6.1 GB) with real-time progress bar and Dev Simulation Guard.

---

## 🛠️ Software Stack & System Requirements

| Component | Technology / Library |
| :--- | :--- |
| **Frontend UI** | HTML5, Vanilla CSS3 (Piano Black Theme), Vanilla JavaScript (Zero Modules) |
| **Desktop Wrapper** | Electron host (`main.js`) |
| **Backend Worker** | Node.js HTTP Server (`server.js`) listening on `http://127.0.0.1:7860` |
| **Multi-Provider Router** | Python 3.12 (`omnirouter.py`) — Hugging Face, OpenRouter, Together AI |
| **Video Render Engine** | Python 3.12 (`render_engine.py`) — MoviePy 2.1, Librosa, PIL, NumPy |
| **CLI Bridge** | Python Subprocess Controller (`engine_bridge.py`) |
| **License** | Apache 2.0 (100% Free and Open Source) |

---

*Open Drama Engine v1.0 — Architecture & MVP Project Board documentation complete.*
