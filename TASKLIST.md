# Open Drama Engine — Video & Animation Production Task List

Welcome Director! Here is our master production roadmap for building **Open Drama Engine**, an AI animation and interactive video production platform. Think of this like configuring a professional video editing suite (NLE) with a Viewport Preview, Multitrack Timeline, Shot List Storyboard, and Scene Compositing Engine.

---

### Phase 1: Studio Suite Setup (NLE Foundation)
- [x] **Task 1.1: Create Video Suite Shell (`index.html`)**
  *Video Term:* Setting up the NLE master workspace layout with Viewport, Timeline, and Shot List panels.
  *Goal:* Clean HTML layout containing the Video Preview Monitor, Shot List Inspector, Timeline Tracks, and Transport Controls.

- [x] **Task 1.2: Design Grading Suite Aesthetics (`index.css`)**
  *Video Term:* Calibrating studio reference monitors and workspace theme for long editing sessions.
  *Goal:* Dark-mode studio theme with glassmorphism panels, crisp 16:9 preview viewport border, and responsive timeline layout.

---

### Phase 2: Preview Viewport & Transport Controls (Monitor Layer)
- [x] **Task 2: Local Asset Loader & Preview Player (`engine.js` / `index.html`)**
  *Video Term:* Importing raw footage clips, sound effects, and graphics into the project bin and loading them into the Program Monitor.
  *Goal:* Wire up the `+ Import Assets` button to pick local `.mp4`, `.png`/`.jpg`, and `.wav`/`.mp3` files, list them dynamically in the Assets sidebar, and load/play them directly in the preview player.

---

### Phase 3: Shot List & Storyboard Sequencer (Script & Logic Engine)
- [x] **Task 3: Timeline Drag & Drop, Clip Resizing & Track Controls (`engine.js` / `index.css`)**
  *Video Term:* Dragging footage clips from the Bin directly onto Timeline tracks, adjusting clip start/end cut points, toggling track Lock/Eye/Mute states, and scrubbing playback.
  *Goal:* Enable drag-and-drop from Assets onto timeline tracks, create resizable timeline clip blocks, sync playhead scrubbing to Program Monitor preview, and lock/hide tracks.

---

### Phase 4: AI Scene Generation & Render Engine (Wan2GP Workflow)
- [x] **Task 4: Wan2GP AI Render Engine & Magnetic Snapping (`engine.js` / `index.html`)**
  *Video Term:* Connecting text-to-video / image-to-video diffusion prompts (Wan 2.1 14B, LTX Video) directly into the rendering pipeline, displaying real-time generation progress overlays, auto-populating timeline tracks, magnetic snapping, and AI idea suggestion generators.
  *Goal:* Add AI prompt inputs + model selector, visual render overlay on the monitor, auto-clip creation onto timeline, magnetic snap toggle (`🧲`), and AI idea prompt generator (`✨ Generate Idea`).

---

### Phase 5: Render Engine & Session Export (State & Polish)
- [x] **Task 5.1: Sequence Project Saver (LocalStorage / JSON Export)**
  *Video Term:* Saving your timeline sequence file so you can reopen your project without losing edits.
  *Goal:* Browser JSON Export/Import and LocalStorage integration to save/load timeline edits, scene selections, and state variables.

- [x] **Task 5.2: Final Assembly Rehearsal & Frame Audit**
  *Video Term:* Quality check pass verifying frame rate stability, audio sync, and scene transition timing.
  *Goal:* End-to-end rehearsal playback test ensuring smooth animation rendering without dropped frames.
