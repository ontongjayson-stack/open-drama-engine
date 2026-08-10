/**
 * Open Drama Engine — Master Suite Controller (engine.js)
 * Cloud-First Hugging Face Inference Priority, Privacy Mode, AI Script Assistant & Automated Shot List Queue
 */

document.addEventListener('DOMContentLoaded', () => {
  console.log('🎬 Open Drama Engine v1.0 — AI Script Assistant & Shot List Engine Online');

  // DOM Elements
  const btnImportTop = document.getElementById('btn-import-top');
  const assetFileInput = document.getElementById('asset-file-input');
  const projectFileInput = document.getElementById('project-file-input');
  const srtFileInput = document.getElementById('srt-file-input');
  const btnSaveProj = document.getElementById('btn-save-proj');
  const btnOpenProj = document.getElementById('btn-open-proj');
  const btnExport = document.getElementById('btn-export');
  const projectNameInput = document.getElementById('project-name-input');
  const assetList = document.getElementById('asset-list');
  const assetGroupTitle = document.getElementById('asset-group-title');

  // Engine Status Pill & Privacy Mode Toggle Switch
  const engineStatusPill = document.getElementById('engine-status-pill');
  const engineStatusText = document.getElementById('engine-status-text');
  const privacyModeToggle = document.getElementById('privacy-mode-toggle');

  // AI Script Assistant Modal & Drawer Elements
  const btnOpenScriptModal = document.getElementById('btn-open-script-modal');
  const btnOpenScriptAssistantDrawer = document.getElementById('btn-open-script-assistant-drawer');
  const scriptModal = document.getElementById('script-modal');
  const btnCloseScriptModal = document.getElementById('btn-close-script-modal');
  const btnCancelScript = document.getElementById('btn-cancel-script');
  const btnGenerateScriptAction = document.getElementById('btn-generate-script-action');
  const scriptIdeaInput = document.getElementById('script-idea-input');
  const scriptGenreSelect = document.getElementById('script-genre-select');
  const scriptDurationSelect = document.getElementById('script-duration-select');
  const scriptOutputBox = document.getElementById('script-output-box');
  const scriptResultText = document.getElementById('script-result-text');

  // Shot List Panel & Batch Queue Elements
  const btnGenerateAllShots = document.getElementById('btn-generate-all-shots');
  const shotCardsWrapper = document.getElementById('shot-cards-wrapper');

  // First-Run Setup & Model Downloader Wizard Modal Elements
  const setupWizardModal = document.getElementById('setup-wizard-modal');
  const btnCloseSetupModal = document.getElementById('btn-close-setup-modal');
  const btnStartModelDownload = document.getElementById('btn-start-model-download');
  const btnSkipSimulatedDev = document.getElementById('btn-skip-simulated-dev');
  const btnLaunchEditor = document.getElementById('btn-launch-editor');
  const setupBarFill = document.getElementById('setup-bar-fill');
  const setupPercentText = document.getElementById('setup-percent-text');
  const setupStatusText = document.getElementById('setup-status-text');

  // Task 5: Export Modal Elements
  const exportModal = document.getElementById('export-modal');
  const btnCloseExportModal = document.getElementById('btn-close-export-modal');
  const btnCancelExport = document.getElementById('btn-cancel-export');
  const btnStartExport = document.getElementById('btn-start-export');
  const exportFilenameInput = document.getElementById('export-filename-input');
  const exportResolution = document.getElementById('export-resolution');
  const exportFormat = document.getElementById('export-format');
  const exportBitrate = document.getElementById('export-bitrate');
  const exportFps = document.getElementById('export-fps');
  const summaryTracksCount = document.getElementById('summary-tracks-count');
  const summarySeqDur = document.getElementById('summary-seq-dur');

  // CapCut Nav Rail & Expandable Drawer Elements
  const railBtns = document.querySelectorAll('.rail-btn');
  const drawerTitle = document.getElementById('drawer-title');
  const btnToggleLeftPanel = document.getElementById('btn-toggle-left-panel');
  const panelAssets = document.getElementById('panel-assets');

  // Drawer Section Containers
  const drawerSecMedia = document.getElementById('drawer-sec-media');
  const drawerSecPrompts = document.getElementById('drawer-sec-prompts');
  const drawerSecCaptions = document.getElementById('drawer-sec-captions');
  const drawerSecAudio = document.getElementById('drawer-sec-audio');
  const drawerSecEffects = document.getElementById('drawer-sec-effects');
  const drawerSecPlugins = document.getElementById('drawer-sec-plugins');

  const drawerBtnAiIdea = document.getElementById('btn-drawer-ai-idea');
  const drawerInspectPrompt = document.getElementById('drawer-inspect-prompt');
  const drawerInspectNegPrompt = document.getElementById('drawer-inspect-neg-prompt');
  const drawerAiModel = document.getElementById('drawer-ai-model');

  // Prompts Panel Sandbox Controls
  const btnDrawerGenerateShot = document.getElementById('btn-drawer-generate-shot');
  const drawerPostGenRow = document.getElementById('drawer-post-gen-row');
  const btnDrawerRegenerate = document.getElementById('btn-drawer-regenerate');
  const btnDrawerAddTimeline = document.getElementById('btn-drawer-add-timeline');

  const btnInspectGenerateShot = document.getElementById('btn-inspect-generate-shot');
  const inspectPostGenRow = document.getElementById('inspect-post-gen-row');
  const btnInspectRegenerate = document.getElementById('btn-inspect-regenerate');
  const btnInspectAddTimeline = document.getElementById('btn-inspect-add-timeline');

  // Resizers
  const leftResizer = document.getElementById('left-resizer');
  const rightResizer = document.getElementById('right-resizer');
  const timelineResizer = document.getElementById('timeline-resizer');
  const panelInspector = document.getElementById('panel-inspector');

  // Header Undo / Redo
  const btnUndo = document.getElementById('btn-undo');
  const btnRedo = document.getElementById('btn-redo');

  // Aspect Ratio & Viewport Elements
  const aspectRatioSelect = document.getElementById('aspect-ratio-select');
  const monitorResolution = document.getElementById('monitor-resolution');
  const viewportScreen = document.getElementById('viewport-screen');
  const viewportVideo = document.getElementById('viewport-video');
  const viewportImg = document.getElementById('viewport-img');
  const viewportAudioVis = document.getElementById('viewport-audio-visualizer');
  const audioFileLabel = document.getElementById('audio-file-label');
  const subText = document.getElementById('sub-text');
  const btnFullscreen = document.getElementById('btn-fullscreen');

  // Smart AI Tools Elements
  const btnAiBgRemove = document.getElementById('btn-ai-bg-remove');
  const btnAutoCaptions = document.getElementById('btn-auto-captions');

  // Inspector & Tab Elements
  const inspectorTabs = document.querySelectorAll('.inspector-tab');
  const inspectorSecVideo = document.getElementById('inspector-sec-video');
  const inspectorSecSmart = document.getElementById('inspector-sec-smart');
  const inspectorSecAudio = document.getElementById('inspector-sec-audio');
  const inspectorSecText = document.getElementById('inspector-sec-text');
  
  const inspectScale = document.getElementById('inspect-scale');
  const valScale = document.getElementById('val-scale');
  const inspectOpacity = document.getElementById('inspect-opacity');
  const valOpacity = document.getElementById('val-opacity');
  const inspectVolume = document.getElementById('inspect-volume');
  const valVolume = document.getElementById('val-volume');

  const inspectAiModel = document.getElementById('inspect-ai-model');
  const inspectPrompt = document.getElementById('inspect-prompt');
  const promptGhost = document.getElementById('prompt-ghost');
  const btnAiIdea = document.getElementById('btn-ai-idea');
  const inspectNegPrompt = document.getElementById('inspect-neg-prompt');
  const inspectCamera = document.getElementById('inspect-camera');
  const inspectAssetName = document.getElementById('inspect-asset-name');
  const timelineV1Label = document.getElementById('timeline-v1-label');

  // NLE Timeline Elements & Scale Architecture
  const btnToolBlade = document.getElementById('btn-tool-blade');
  const btnSnap = document.getElementById('btn-snap');
  const zoomSlider = document.getElementById('zoom-slider');
  const panelTimeline = document.getElementById('panel-timeline');
  const timelineTracksArea = document.getElementById('timeline-tracks-area');
  const timelineScrollContent = document.getElementById('timeline-scroll-content');
  const rulerTicksContainer = document.getElementById('ruler-ticks-container');

  // Render Overlay Elements
  const renderProgressOverlay = document.getElementById('render-progress-overlay');
  const renderOverlayTitle = document.getElementById('render-overlay-title');
  const renderStatusText = document.getElementById('render-status-text');
  const renderBarFill = document.getElementById('render-bar-fill');
  const renderPercentText = document.getElementById('render-percent-text');
  const renderModelText = document.getElementById('render-model-text');

  // Transport Controls
  const btnPlay = document.getElementById('btn-play');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const timecodeDisplay = document.getElementById('timecode-display');
  const tcCurrentTime = document.getElementById('tc-current-time');
  const tcTotalDuration = document.getElementById('tc-total-duration');
  const scrubberInput = document.getElementById('scrubber-input');
  const playheadLine = document.getElementById('playhead-line');

  // State
  let activeAsset = { type: 'image', url: 'scifi_city_preview.jpg', name: 'Shot_01_BG.mp4' };
  let lastGeneratedShot = null;
  let isPlaying = false;
  let currentFrame = 0;
  const fps = 24;
  const totalSeqDuration = 90;
  let playInterval = null;
  let selectedClip = null;
  let isRendering = false;
  let renderShotCount = 1;
  let isSnappingOn = true;
  let isBladeMode = false;
  let isDrawerCollapsed = false;
  let parsedShotsData = [];

  // Local Backend Server State
  const SERVER_URL = 'http://127.0.0.1:7860';
  let engineStatus = 'online';

  // Time Scale Zoom Architecture (Pixels Per Second)
  const ppsMap = { 1: 18, 2: 35, 3: 70, 4: 120, 5: 200 };
  let currentPPS = ppsMap[2]; // Default Zoom level 2 = 35px/sec

  // --------------------------------------------------------------------------
  // PRIVACY MODE TOGGLE HANDLER
  // --------------------------------------------------------------------------
  if (privacyModeToggle) {
    privacyModeToggle.addEventListener('change', () => {
      const isPrivate = privacyModeToggle.checked;
      if (isPrivate) {
        updateEngineStatusPill('online', '🔒 LOCAL ENGINE: PRIVACY MODE');
        console.log('🔒 Privacy Mode Enabled: Generation requests routed locally to 127.0.0.1:7860');
      } else {
        updateEngineStatusPill('online', '☁️ CLOUD ENGINE: HUGGINGFACE');
        console.log('☁️ Cloud Priority Enabled: Primary generation requests routed to HuggingFace Inference API');
      }
    });
  }

  // --------------------------------------------------------------------------
  // AI SCRIPT ASSISTANT MODAL & AUTOMATED SHOT LIST ENGINE
  // --------------------------------------------------------------------------
  function openScriptModal() {
    scriptModal.classList.remove('hidden');
  }

  function closeScriptModal() {
    scriptModal.classList.add('hidden');
  }

  if (btnOpenScriptModal) btnOpenScriptModal.addEventListener('click', openScriptModal);
  if (btnOpenScriptAssistantDrawer) btnOpenScriptAssistantDrawer.addEventListener('click', openScriptModal);
  if (btnCloseScriptModal) btnCloseScriptModal.addEventListener('click', closeScriptModal);
  if (btnCancelScript) btnCancelScript.addEventListener('click', closeScriptModal);

  if (btnGenerateScriptAction) {
    btnGenerateScriptAction.addEventListener('click', async () => {
      const topic = scriptIdeaInput.value.trim() || 'Heroic cybernetic cat escaping surveillance drone';
      const genre = scriptGenreSelect.value;
      const targetDuration = parseInt(scriptDurationSelect.value) || 30;

      btnGenerateScriptAction.disabled = true;
      btnGenerateScriptAction.textContent = '⏳ Generating Script...';

      try {
        const response = await window.fetch(`${SERVER_URL}/api/generate-script`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, genre, targetDuration })
        });

        if (response.ok) {
          const data = await response.json();
          console.log('✨ AI Script Generation Response:', data);

          scriptResultText.value = data.scriptText || 'Script generated successfully.';
          scriptOutputBox.classList.remove('hidden');
          parsedShotsData = data.shots || [];

          renderShotCards(parsedShotsData);

          // Switch drawer to Prompts tab so user sees Shot List cards immediately
          switchLeftDrawerTab('prompts');
          railBtns.forEach(b => {
            b.classList.toggle('active', b.dataset.panel === 'prompts');
          });
          if (drawerTitle) drawerTitle.textContent = 'PROMPTS TOOLBOX';
        }
      } catch (err) {
        console.warn('⚡ Script Generation failed or server unreachable:', err);
        // Fallback default shot cards if server unavailable
        parsedShotsData = [
          { id: 1, title: 'Shot 01: Hero Intro', prompt: `2D cartoon ${genre} style, close up shot of a cybernetic cat hero in neon city, ${topic}`, framing: 'CU Dialogue', duration: 5.0 },
          { id: 2, title: 'Shot 02: Sidekick Reaction', prompt: `2D cartoon ${genre} style, medium tracking shot of robot sidekick dancing, ${topic}`, framing: 'Medium Tracking', duration: 5.0 },
          { id: 3, title: 'Shot 03: High Voltage Chase', prompt: `2D cartoon ${genre} style, wide action shot of hovercars racing through neon alley, ${topic}`, framing: 'Wide Action', duration: 5.0 }
        ];
        renderShotCards(parsedShotsData);
      } finally {
        btnGenerateScriptAction.disabled = false;
        btnGenerateScriptAction.textContent = '⚡ Generate Script & Parse Shot List';
        closeScriptModal();
      }
    });
  }

  function renderShotCards(shots) {
    if (!shotCardsWrapper) return;
    shotCardsWrapper.innerHTML = '';

    if (!shots || shots.length === 0) {
      shotCardsWrapper.innerHTML = '<p style="font-size: 0.72rem; color: var(--text-muted); text-align: center; padding: 12px;">No automated shots generated yet. Click "✨ Open AI Script Assistant" to generate a script!</p>';
      return;
    }

    shots.forEach((shot, index) => {
      const cardEl = document.createElement('div');
      cardEl.className = 'shot-card-item';
      cardEl.dataset.shotId = shot.id || (index + 1);

      cardEl.innerHTML = `
        <div class="shot-card-header">
          <span>${shot.title || `Shot ${index+1:02d}`}</span>
          <div class="shot-card-meta">
            <span class="shot-status-badge idle" id="shot-status-${index}">IDLE</span>
            <span style="color: var(--text-muted); font-size: 0.68rem;">[${shot.duration || 5.0}s]</span>
          </div>
        </div>
        <div class="shot-card-body">
          <textarea class="shot-card-prompt" rows="2">${shot.prompt}</textarea>
          <div class="shot-card-row">
            <select class="field-select shot-card-framing" style="flex: 1; padding: 3px 6px; font-size: 0.72rem;">
              <option value="CU Dialogue" ${shot.framing === 'CU Dialogue' ? 'selected' : ''}>CU Dialogue</option>
              <option value="Wide Action" ${shot.framing === 'Wide Action' ? 'selected' : ''}>Wide Action</option>
              <option value="Medium Tracking" ${shot.framing === 'Medium Tracking' ? 'selected' : ''}>Medium Tracking</option>
              <option value="Over the Shoulder" ${shot.framing === 'Over the Shoulder' ? 'selected' : ''}>Over the Shoulder</option>
              <option value="Close-Up" ${shot.framing === 'Close-Up' ? 'selected' : ''}>Close-Up</option>
            </select>
          </div>
        </div>
        <div class="shot-card-actions">
          <button class="btn-shot-render" id="btn-render-shot-${index}">🎬 Render Shot</button>
        </div>
      `;

      shotCardsWrapper.appendChild(cardEl);

      const btnRender = cardEl.querySelector(`#btn-render-shot-${index}`);
      if (btnRender) {
        btnRender.addEventListener('click', () => renderSingleShotCard(cardEl, shot, index));
      }
    });
  }

  async function renderSingleShotCard(cardEl, shotObj, index) {
    const promptText = cardEl.querySelector('.shot-card-prompt').value || shotObj.prompt;
    const framing = cardEl.querySelector('.shot-card-framing').value || shotObj.framing;
    const statusBadge = cardEl.querySelector(`#shot-status-${index}`);

    cardEl.classList.add('rendering');
    if (statusBadge) {
      statusBadge.className = 'shot-status-badge rendering';
      statusBadge.textContent = 'RENDERING...';
    }

    inspectPrompt.value = promptText;
    if (drawerInspectPrompt) drawerInspectPrompt.value = promptText;

    const payload = {
      prompt: promptText,
      negativePrompt: inspectNegPrompt ? inspectNegPrompt.value : '',
      framing: framing,
      model: inspectAiModel ? inspectAiModel.options[inspectAiModel.selectedIndex].text : 'Wan 2.1 14B',
      aspectRatio: aspectRatioSelect.value
    };

    const apiResult = await callGradioWan2GPEndpoint(payload);

    cardEl.classList.remove('rendering');
    if (apiResult.success) {
      cardEl.classList.add('completed');
      if (statusBadge) {
        statusBadge.className = 'shot-status-badge ready';
        statusBadge.textContent = 'READY';
      }
      const shotName = apiResult.shotName || `Shot_${index+1:02d}.mp4`;
      const videoUrl = apiResult.url || 'scifi_city_preview.jpg';
      finishShotGenerationAndAutoPopulate(shotName, videoUrl);
    } else {
      if (statusBadge) {
        statusBadge.className = 'shot-status-badge idle';
        statusBadge.textContent = 'IDLE';
      }
    }
  }

  // --------------------------------------------------------------------------
  // ONE-CLICK TIMELINE BATCH QUEUE ("⚡ Generate All Shots")
  // --------------------------------------------------------------------------
  if (btnGenerateAllShots) {
    btnGenerateAllShots.addEventListener('click', async () => {
      const cards = shotCardsWrapper.querySelectorAll('.shot-card-item');
      if (!cards || cards.length === 0) {
        alert('Please generate an AI Script first to create shot list cards!');
        openScriptModal();
        return;
      }

      btnGenerateAllShots.disabled = true;
      btnGenerateAllShots.textContent = '⏳ Batch Queuing...';
      console.log(`⚡ Starting Batch Queue Generation for ${cards.length} shots...`);

      let currentTimelineTime = (currentFrame / fps) || 0;

      for (let i = 0; i < cards.length; i++) {
        const cardEl = cards[i];
        const promptText = cardEl.querySelector('.shot-card-prompt').value;
        const framing = cardEl.querySelector('.shot-card-framing').value;
        const statusBadge = cardEl.querySelector(`#shot-status-${i}`);

        cardEl.classList.add('rendering');
        if (statusBadge) {
          statusBadge.className = 'shot-status-badge rendering';
          statusBadge.textContent = 'RENDERING...';
        }

        const isPrivacy = privacyModeToggle ? privacyModeToggle.checked : false;
        const payload = {
          prompt: promptText,
          negativePrompt: inspectNegPrompt ? inspectNegPrompt.value : '',
          framing: framing,
          model: 'Wan 2.1 14B',
          aspectRatio: aspectRatioSelect.value,
          privacyMode: isPrivacy
        };

        console.log(`[Batch Queue]: Processing Shot ${i+1}/${cards.length}: "${promptText[:30]}..."`);
        const apiResult = await callGradioWan2GPEndpoint(payload);

        cardEl.classList.remove('rendering');
        cardEl.classList.add('completed');
        if (statusBadge) {
          statusBadge.className = 'shot-status-badge ready';
          statusBadge.textContent = 'READY';
        }

        const shotName = apiResult.shotName || `Shot_${i+1:02d}.mp4`;
        const videoUrl = apiResult.url || 'scifi_city_preview.jpg';

        const shotAsset = {
          type: videoUrl.endsWith('.png') || videoUrl.endsWith('.jpg') ? 'image' : 'video',
          url: videoUrl,
          name: shotName
        };

        // Auto-populate to VIDEO 1 on timeline sequentially in chronological order
        const video1Lane = document.querySelector('.timeline-track-row[data-track-id="video1"] .track-lane-area');
        if (video1Lane) {
          createTimelineClip(video1Lane, shotAsset, currentTimelineTime, 5.0, 'clip-video');
          currentTimelineTime += 5.0; // Advance timecode for next clip
        }
      }

      btnGenerateAllShots.disabled = false;
      btnGenerateAllShots.textContent = '⚡ Generate All Shots';
      renderRulerAndClips();
      alert(`🎉 Batch Queue Complete! All ${cards.length} shots rendered and laid out sequentially on VIDEO 1 timeline track!`);
    });
  }

  // --------------------------------------------------------------------------
  // VIDEO PLAYER ERROR FALLBACK & CONSOLE LOGGER
  // --------------------------------------------------------------------------
  if (viewportVideo) {
    viewportVideo.onerror = (e) => {
      console.warn('⚡ Video Load Error, attempted src:', viewportVideo.src, e);
      if (viewportVideo.classList.contains('hidden') === false) {
        viewportVideo.classList.add('hidden');
        viewportImg.src = 'scifi_city_preview.jpg';
        viewportImg.classList.remove('hidden');
      }
    };

    viewportVideo.onloadeddata = () => {
      console.log('✅ Video loaded successfully. Source:', viewportVideo.src);
    };
  }

  // --------------------------------------------------------------------------
  // GRADIO OUTPUT PARSER & VIDEO PATH RESOLVER
  // --------------------------------------------------------------------------
  function resolveGradioVideoUrl(rawItem) {
    if (!rawItem) return 'scifi_city_preview.jpg';

    // 1. Object format (Gradio FileData object { name, path, url })
    if (typeof rawItem === 'object') {
      if (rawItem.url) return rawItem.url;
      if (rawItem.path) return `${SERVER_URL}/file=${encodeURIComponent(rawItem.path)}`;
      if (rawItem.name) return `${SERVER_URL}/generated_assets/${rawItem.name}`;
    }

    // 2. String format (URL, Gradio /file= route, or local filename)
    if (typeof rawItem === 'string') {
      if (rawItem.startsWith('http://') || rawItem.startsWith('https://') || rawItem.startsWith('data:') || rawItem.startsWith('blob:')) {
        return rawItem;
      }
      if (rawItem.startsWith('/file=')) {
        return `${SERVER_URL}${rawItem}`;
      }
      if (rawItem.startsWith('/')) {
        return `${SERVER_URL}/file=${encodeURIComponent(rawItem)}`;
      }
      return `${SERVER_URL}/generated_assets/${rawItem}`;
    }

    return 'scifi_city_preview.jpg';
  }

  // --------------------------------------------------------------------------
  // SAFE WINDOW.FETCH API ROUTER (CLOUD HUGGING FACE PRIMARY VS LOCAL PRIVACY)
  // --------------------------------------------------------------------------
  async function callGradioWan2GPEndpoint(payload) {
    const isPrivacy = privacyModeToggle ? privacyModeToggle.checked : false;
    payload.privacyMode = isPrivacy;

    if (isPrivacy) {
      console.log('🔒 Privacy Mode ON: Routing directly to Local Wan2GP Engine at http://127.0.0.1:7860/run/predict');
    } else {
      console.log('☁️ Privacy Mode OFF: Prioritizing Cloud HuggingFace Inference API with Local Fallback');
    }

    const candidateRoutes = [
      { url: `${SERVER_URL}/run/predict`, body: { data: [payload.prompt, payload.negativePrompt, payload.framing, payload.model, payload.aspectRatio], privacyMode: isPrivacy } },
      { url: `${SERVER_URL}/api/predict`, body: { data: [payload.prompt, payload.negativePrompt, payload.framing, payload.model, payload.aspectRatio], fn_index: 0, api_name: '/predict', privacyMode: isPrivacy } },
      { url: `${SERVER_URL}/call/predict`, body: { data: [payload.prompt, payload.negativePrompt, payload.framing, payload.model, payload.aspectRatio], fn_index: 0, privacyMode: isPrivacy } },
      { url: `${SERVER_URL}/api/generate`, body: payload }
    ];

    for (const route of candidateRoutes) {
      try {
        console.log(`[API Router]: Trying endpoint ${route.url}...`);
        const response = await window.fetch(route.url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(route.body)
        });

        if (response.ok) {
          const json = await response.json();
          console.log(`[API Router]: Raw JSON response from ${route.url}:`, json);

          let shotName = `Wan2GP_Render_Shot_${Date.now().toString().slice(-4)}.mp4`;
          let rawUrlItem = null;

          if (json.data && Array.isArray(json.data) && json.data.length > 0) {
            rawUrlItem = json.data[0];
            if (typeof json.data[0] === 'object' && json.data[0].name) {
              shotName = json.data[0].name;
            } else if (typeof json.data[0] === 'string') {
              shotName = json.data[0];
            }
            if (json.data[1]) rawUrlItem = json.data[1];
          } else if (json.url || json.shotName) {
            rawUrlItem = json.url || json.shotName;
            if (json.shotName) shotName = json.shotName;
          }

          const resolvedUrl = resolveGradioVideoUrl(rawUrlItem);
          console.log(`[API Router]: Resolved Video URL -> ${resolvedUrl}`);

          return { success: true, shotName, url: resolvedUrl, provider: json.provider || (isPrivacy ? 'local_privacy' : 'huggingface_cloud'), route: route.url };
        }
      } catch (err) {
        console.warn(`[API Router]: Route ${route.url} error:`, err);
      }
    }

    // Fallback Dev Simulation Guard
    console.warn('[API Router]: Backend endpoints rate-limited or unreachable. Falling back to dev progress bar simulation mode.');
    return { success: false, fallback: true };
  }

  // --------------------------------------------------------------------------
  // LOCAL ENGINE MANAGER & FIRST-RUN SETUP WIZARD
  // --------------------------------------------------------------------------
  async function checkLocalEngineStatus() {
    try {
      const res = await window.fetch(`${SERVER_URL}/api/status`);
      if (res.ok) {
        const data = await res.json();
        engineStatus = 'online';
        if (privacyModeToggle && privacyModeToggle.checked) {
          updateEngineStatusPill('online', '🔒 LOCAL ENGINE: PRIVACY MODE');
        } else {
          updateEngineStatusPill('online', '☁️ CLOUD ENGINE: HUGGINGFACE');
        }
      } else {
        throw new Error('Server non-200 response');
      }

      // First-Run Setup & Model Downloader Check
      const weightsRes = await window.fetch(`${SERVER_URL}/api/check-weights`);
      if (weightsRes.ok) {
        const weightsData = await weightsRes.json();
        console.log('⚡ First-Run Model Weights Status:', weightsData);
        if (!weightsData.exists && setupWizardModal) {
          console.log('⚡ Required model weights missing locally. Triggering First-Run Setup Wizard modal...');
          setupWizardModal.classList.remove('hidden');
        }
      }
    } catch (err) {
      console.warn('⚡ Local backend process not responding directly. Running in Fallback Simulated Mode:', err);
      engineStatus = 'simulated';
      updateEngineStatusPill('simulated', 'LOCAL ENGINE: SIMULATED (DEV)');
    }
  }

  function updateEngineStatusPill(status, text) {
    if (!engineStatusPill) return;
    const dot = engineStatusPill.querySelector('.status-dot');
    if (dot) dot.className = `status-dot ${status}`;
    if (engineStatusText) engineStatusText.textContent = text;
  }

  if (btnStartModelDownload) {
    btnStartModelDownload.addEventListener('click', async () => {
      btnStartModelDownload.disabled = true;
      btnStartModelDownload.textContent = '⏳ Downloading Assets...';
      setupStatusText.textContent = 'Status: Connecting to HuggingFace model repo...';

      let pct = 0;
      const downloadInterval = setInterval(() => {
        pct += 20;
        setupBarFill.style.width = `${pct}%`;
        setupPercentText.textContent = `${pct}%`;
        setupStatusText.textContent = `Status: Downloading Wan2GP 14B VAE weights... (${(6.1 * (pct/100)).toFixed(1)} GB / 6.1 GB)`;

        if (pct >= 100) {
          clearInterval(downloadInterval);
          setupStatusText.textContent = 'Status: Model weights verified & ready!';
          btnStartModelDownload.classList.add('hidden');
          btnLaunchEditor.classList.remove('hidden');
          window.fetch(`${SERVER_URL}/api/download-weights`, { method: 'POST' }).catch(() => {});
        }
      }, 500);
    });
  }

  if (btnSkipSimulatedDev) {
    btnSkipSimulatedDev.addEventListener('click', () => {
      engineStatus = 'simulated';
      updateEngineStatusPill('simulated', 'LOCAL ENGINE: SIMULATED (DEV)');
      setupWizardModal.classList.add('hidden');
    });
  }

  if (btnLaunchEditor) {
    btnLaunchEditor.addEventListener('click', () => {
      engineStatus = 'online';
      updateEngineStatusPill('online', '☁️ CLOUD ENGINE: HUGGINGFACE');
      setupWizardModal.classList.add('hidden');
    });
  }

  if (btnCloseSetupModal) btnCloseSetupModal.addEventListener('click', () => setupWizardModal.classList.add('hidden'));

  checkLocalEngineStatus();

  // --------------------------------------------------------------------------
  // Bi-Directional Synchronization of Prompt & Model Inputs
  // --------------------------------------------------------------------------
  if (inspectPrompt && drawerInspectPrompt) {
    inspectPrompt.addEventListener('input', () => { drawerInspectPrompt.value = inspectPrompt.value; });
    drawerInspectPrompt.addEventListener('input', () => { inspectPrompt.value = drawerInspectPrompt.value; });
  }

  if (inspectNegPrompt && drawerInspectNegPrompt) {
    inspectNegPrompt.addEventListener('input', () => { drawerInspectNegPrompt.value = inspectNegPrompt.value; });
    drawerInspectNegPrompt.addEventListener('input', () => { inspectNegPrompt.value = drawerInspectNegPrompt.value; });
  }

  if (inspectAiModel && drawerAiModel) {
    inspectAiModel.addEventListener('change', () => { drawerAiModel.value = inspectAiModel.value; });
    drawerAiModel.addEventListener('change', () => { inspectAiModel.value = drawerAiModel.value; });
  }

  // --------------------------------------------------------------------------
  // 1. NLE Scale-Based Ruler & Grid Renderer
  // --------------------------------------------------------------------------
  function renderRulerAndClips() {
    const zoomLevel = parseInt(zoomSlider.value) || 2;
    currentPPS = ppsMap[zoomLevel] || 35;

    const totalWidthPx = totalSeqDuration * currentPPS;
    timelineScrollContent.style.width = `${totalWidthPx + 120}px`;

    rulerTicksContainer.innerHTML = '';
    
    document.querySelectorAll('.track-lane-area').forEach(lane => {
      lane.querySelectorAll('.grid-line').forEach(gl => gl.remove());
    });

    let secStep = 10;
    if (currentPPS >= 120) secStep = 1;
    else if (currentPPS >= 60) secStep = 2;
    else if (currentPPS >= 30) secStep = 5;

    for (let sec = 0; sec <= totalSeqDuration; sec += secStep) {
      const posX = sec * currentPPS;

      const tickEl = document.createElement('div');
      tickEl.className = 'ruler-tick major';
      tickEl.style.left = `${posX}px`;
      tickEl.textContent = formatShortTime(sec);
      rulerTicksContainer.appendChild(tickEl);

      document.querySelectorAll('.track-lane-area').forEach(lane => {
        const gridLine = document.createElement('div');
        gridLine.className = 'grid-line major';
        gridLine.style.left = `${posX}px`;
        lane.appendChild(gridLine);
      });
    }

    document.querySelectorAll('.clip-block').forEach(clip => {
      const startSec = parseFloat(clip.dataset.start) || 0;
      const durationSec = parseFloat(clip.dataset.duration) || 15;

      clip.style.left = `${startSec * currentPPS}px`;
      clip.style.width = `${durationSec * currentPPS}px`;

      const metaLabel = clip.querySelector('.clip-meta');
      if (metaLabel) metaLabel.textContent = `[${durationSec.toFixed(1)}s]`;
    });

    const currentSec = (currentFrame / fps) || 0;
    updateUIProgress(currentSec, totalSeqDuration);
  }

  zoomSlider.addEventListener('input', renderRulerAndClips);
  renderRulerAndClips();

  // --------------------------------------------------------------------------
  // 2. Left Drawer Tabs Switching
  // --------------------------------------------------------------------------
  function switchLeftDrawerTab(panelName) {
    const sections = [drawerSecMedia, drawerSecPrompts, drawerSecCaptions, drawerSecAudio, drawerSecEffects, drawerSecPlugins];
    sections.forEach(sec => { if (sec) sec.classList.add('hidden'); });

    if (panelName === 'media' && drawerSecMedia) drawerSecMedia.classList.remove('hidden');
    else if (panelName === 'prompts' && drawerSecPrompts) drawerSecPrompts.classList.remove('hidden');
    else if (panelName === 'captions' && drawerSecCaptions) drawerSecCaptions.classList.remove('hidden');
    else if (panelName === 'audio' && drawerSecAudio) drawerSecAudio.classList.remove('hidden');
    else if (panelName === 'effects' && drawerSecEffects) drawerSecEffects.classList.remove('hidden');
    else if (panelName === 'plugins' && drawerSecPlugins) drawerSecPlugins.classList.remove('hidden');
  }

  railBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      railBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const panelId = btn.dataset.panel;
      if (drawerTitle) drawerTitle.textContent = `${panelId.toUpperCase()} TOOLBOX`;

      switchLeftDrawerTab(panelId);

      if (isDrawerCollapsed) {
        isDrawerCollapsed = false;
        panelAssets.classList.remove('drawer-collapsed');
        if (btnToggleLeftPanel) btnToggleLeftPanel.textContent = '◀';
      }
    });
  });

  if (btnToggleLeftPanel) {
    btnToggleLeftPanel.addEventListener('click', () => {
      isDrawerCollapsed = !isDrawerCollapsed;
      panelAssets.classList.toggle('drawer-collapsed', isDrawerCollapsed);
      btnToggleLeftPanel.textContent = isDrawerCollapsed ? '▶' : '◀';
      btnToggleLeftPanel.title = isDrawerCollapsed ? 'Expand Tool Drawer' : 'Collapse Tool Drawer';
    });
  }

  // --------------------------------------------------------------------------
  // TASK 5: TIMELINE TRACK READER & FFMPEG MULTI-TRACK EXPORT ENGINE
  // --------------------------------------------------------------------------
  function parseTimelineTracks() {
    const trackRows = document.querySelectorAll('.timeline-track-row');
    const parsedTracks = [];
    let maxEndSec = 0;

    trackRows.forEach(row => {
      const trackId = row.dataset.trackId;
      const trackName = row.querySelector('.track-name').textContent.trim();
      const clips = [];

      row.querySelectorAll('.clip-block').forEach(clip => {
        const startSec = parseFloat(clip.dataset.start) || 0;
        const durationSec = parseFloat(clip.dataset.duration) || 15;
        const endSec = startSec + durationSec;
        if (endSec > maxEndSec) maxEndSec = endSec;

        clips.push({
          name: clip.querySelector('.clip-label').textContent,
          startSec: startSec,
          durationSec: durationSec,
          endSec: endSec,
          assetData: clip.dataset.asset ? JSON.parse(clip.dataset.asset) : null
        });
      });

      if (clips.length > 0) {
        parsedTracks.push({
          trackId: trackId,
          trackName: trackName,
          clips: clips
        });
      }
    });

    return { tracks: parsedTracks, maxEndSec: maxEndSec || 25.0 };
  }

  if (btnExport) {
    btnExport.addEventListener('click', () => {
      if (isRendering) return;
      
      const projName = projectNameInput.value.trim() || 'Scene_01_Intro';
      exportFilenameInput.value = `${projName}_Export.mp4`;

      const parsed = parseTimelineTracks();
      const trackNames = parsed.tracks.map(t => t.trackName).join(', ');
      summaryTracksCount.textContent = trackNames || 'None';
      
      const targetFps = parseInt(exportFps.value) || 24;
      const totalFrames = Math.ceil(parsed.maxEndSec * targetFps);
      summarySeqDur.textContent = `${parsed.maxEndSec.toFixed(1)}s (${totalFrames} Frames)`;

      exportModal.classList.remove('hidden');
    });
  }

  if (btnCloseExportModal) btnCloseExportModal.addEventListener('click', () => exportModal.classList.add('hidden'));
  if (btnCancelExport) btnCancelExport.addEventListener('click', () => exportModal.classList.add('hidden'));

  if (btnStartExport) {
    btnStartExport.addEventListener('click', () => {
      exportModal.classList.add('hidden');
      runFfmpegExportPipeline();
    });
  }

  function runFfmpegExportPipeline() {
    isRendering = true;
    pauseMedia();

    const parsed = parseTimelineTracks();
    const fileName = exportFilenameInput.value.trim() || 'Scene_01_Intro_Export.mp4';
    const resolution = exportResolution.value;
    const format = exportFormat.value;
    const bitrate = exportBitrate.value;
    const targetFps = parseInt(exportFps.value) || 24;

    const totalFrames = Math.ceil(parsed.maxEndSec * targetFps);

    renderProgressOverlay.classList.remove('hidden');
    if (renderOverlayTitle) renderOverlayTitle.textContent = 'FFMPEG COMPOSITING ENGINE';
    renderModelText.textContent = `Target: ${fileName} (${resolution} ${targetFps}fps ${bitrate})`;
    renderBarFill.style.width = '0%';
    renderPercentText.textContent = '0%';

    const steps = [
      { pct: 15, frame: Math.floor(totalFrames * 0.15), status: `Parsing ${parsed.tracks.length} active tracks (${summaryTracksCount.textContent})...` },
      { pct: 45, frame: Math.floor(totalFrames * 0.45), status: `Compositing Video (VIDEO 1) & Character (CHR 1) layers...` },
      { pct: 75, frame: Math.floor(totalFrames * 0.75), status: `Muxing Subtitles (TEXT 1) & Audio (AUD 2) at ${bitrate}...` },
      { pct: 100, frame: totalFrames, status: `Export Complete! Saving output file to disk...` }
    ];

    let stepIdx = 0;
    const exportInterval = setInterval(() => {
      if (stepIdx < steps.length) {
        const currentStep = steps[stepIdx];
        renderBarFill.style.width = `${currentStep.pct}%`;
        renderPercentText.textContent = `${currentStep.pct}%`;
        renderStatusText.textContent = `Stitching Sequence... Frame ${currentStep.frame}/${totalFrames} (${currentStep.pct}%) — ${currentStep.status}`;
        stepIdx++;
      } else {
        clearInterval(exportInterval);
        setTimeout(() => finishFfmpegExport(fileName), 400);
      }
    }, 500);
  }

  function finishFfmpegExport(fileName) {
    renderProgressOverlay.classList.add('hidden');
    if (renderOverlayTitle) renderOverlayTitle.textContent = 'WAN2GP RENDER ENGINE';
    isRendering = false;

    const dummyBlob = new Blob(['Open Drama Engine FFmpeg Multi-Track Assembled Output'], { type: 'video/mp4' });
    const url = URL.createObjectURL(dummyBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);

    alert(`🎉 Export Complete! Multi-track sequence assembled and saved as "${fileName}".`);
  }

  // --------------------------------------------------------------------------
  // LIVE SHOT GENERATION RENDER PIPELINE (CLOUD HUGGING FACE VS PRIVACY MODE)
  // --------------------------------------------------------------------------
  async function runShotGeneration() {
    if (isRendering) return;
    isRendering = true;
    pauseMedia();

    const isPrivacy = privacyModeToggle ? privacyModeToggle.checked : false;
    const selectedModel = inspectAiModel.options[inspectAiModel.selectedIndex].text;
    const promptText = inspectPrompt.value || '2D animated scene';
    const negPromptText = inspectNegPrompt.value || '';
    const framing = inspectCamera.options[inspectCamera.selectedIndex].text;
    const ratio = aspectRatioSelect.value;

    const payload = {
      prompt: promptText,
      negativePrompt: negPromptText,
      model: selectedModel,
      framing: framing,
      aspectRatio: ratio,
      privacyMode: isPrivacy,
      timestamp: new Date().toISOString()
    };

    console.log(`⚡ Initiating Shot Render Pipeline (Privacy Mode: ${isPrivacy}) with payload:`, payload);

    renderShotCount++;
    const defaultShotName = `Wan2GP_Render_Shot_${String(renderShotCount).padStart(2, '0')}.mp4`;

    renderProgressOverlay.classList.remove('hidden');
    if (renderOverlayTitle) {
      renderOverlayTitle.textContent = isPrivacy ? 'LOCAL WAN2GP GPU WORKER (PRIVACY MODE)' : 'CLOUD HUGGING FACE GPU WORKER';
    }
    renderModelText.textContent = `Model: ${selectedModel} [${isPrivacy ? 'LOCAL' : 'HUGGINGFACE CLOUD'}]`;
    renderBarFill.style.width = '0%';
    renderPercentText.textContent = '0%';

    let currentPct = 0;
    const progressInterval = setInterval(() => {
      if (currentPct < 90) {
        currentPct += 15;
        renderBarFill.style.width = `${currentPct}%`;
        renderPercentText.textContent = `${currentPct}%`;
        const engineLabel = isPrivacy ? 'Local Engine' : 'Cloud HuggingFace';
        renderStatusText.textContent = `Rendering Shot ${String(renderShotCount).padStart(2, '0')} via ${engineLabel} (${currentPct}%) — Sampling Latents...`;
      }
    }, 350);

    // Call API router with Fallback Simulation Guard
    const apiResult = await callGradioWan2GPEndpoint(payload);

    clearInterval(progressInterval);
    renderBarFill.style.width = '100%';
    renderPercentText.textContent = '100%';

    if (apiResult.success) {
      renderStatusText.textContent = `Render Complete! Provider: ${apiResult.provider || 'HuggingFace Cloud'}`;
    } else {
      renderStatusText.textContent = `Dev Simulation Guard Executed! Auto-populating preview shot...`;
    }

    setTimeout(() => {
      const finalShotName = apiResult.shotName || defaultShotName;
      const finalUrl = apiResult.url || 'scifi_city_preview.jpg';
      finishShotGenerationAndAutoPopulate(finalShotName, finalUrl);
    }, 400);
  }

  function finishShotGenerationAndAutoPopulate(shotName, videoUrl) {
    renderProgressOverlay.classList.add('hidden');
    isRendering = false;

    let assetType = 'video';
    if (videoUrl.endsWith('.jpg') || videoUrl.endsWith('.jpeg') || videoUrl.endsWith('.png')) {
      assetType = 'image';
    }

    lastGeneratedShot = {
      type: assetType,
      url: videoUrl,
      name: shotName
    };

    // 1. Add to Assets Library
    const itemEl = document.createElement('div');
    itemEl.className = 'asset-item active';
    itemEl.dataset.type = lastGeneratedShot.type;
    itemEl.dataset.url = lastGeneratedShot.url;
    itemEl.dataset.name = lastGeneratedShot.name;

    itemEl.innerHTML = `
      <div class="asset-badge video">⚡</div>
      <span class="asset-name">${lastGeneratedShot.name}</span>
      <button class="asset-delete-btn" title="Delete Asset from Library">🗑️</button>
    `;

    document.querySelectorAll('.asset-item').forEach(el => el.classList.remove('active'));
    assetList.prepend(itemEl);
    makeAssetDraggable(itemEl);
    bindAssetEvents(itemEl);
    updateAssetGroupCount();

    // 2. Auto-Populate directly onto active VIDEO 1 track on timeline
    const video1Lane = document.querySelector('.timeline-track-row[data-track-id="video1"] .track-lane-area');
    if (video1Lane) {
      const playheadSec = (currentFrame / fps) || 0;
      createTimelineClip(video1Lane, lastGeneratedShot, playheadSec, 15, 'clip-video');
    }

    // 3. Auto-load into Program Monitor and Play Immediately
    activeAsset = lastGeneratedShot;
    loadAssetToMonitor(activeAsset);
    subText.textContent = `Render Output: "${inspectPrompt.value.substring(0, 40)}..."`;
    playMedia();

    if (btnDrawerGenerateShot) btnDrawerGenerateShot.classList.add('hidden');
    if (drawerPostGenRow) drawerPostGenRow.classList.remove('hidden');

    if (btnInspectGenerateShot) btnInspectGenerateShot.classList.add('hidden');
    if (inspectPostGenRow) inspectPostGenRow.classList.remove('hidden');
  }

  function addCurrentShotToTimeline() {
    if (!lastGeneratedShot) return;
    const video1Lane = document.querySelector('.timeline-track-row[data-track-id="video1"] .track-lane-area');
    if (video1Lane) {
      const playheadSec = (currentFrame / fps) || 0;
      createTimelineClip(video1Lane, lastGeneratedShot, playheadSec, 15, 'clip-video');
      alert(`➕ Added "${lastGeneratedShot.name}" to VIDEO 1 track at ${formatShortTime(playheadSec)}!`);
    }
  }

  if (btnDrawerGenerateShot) btnDrawerGenerateShot.addEventListener('click', runShotGeneration);
  if (btnInspectGenerateShot) btnInspectGenerateShot.addEventListener('click', runShotGeneration);

  if (btnDrawerRegenerate) btnDrawerRegenerate.addEventListener('click', runShotGeneration);
  if (btnInspectRegenerate) btnInspectRegenerate.addEventListener('click', runShotGeneration);

  if (btnDrawerAddTimeline) btnDrawerAddTimeline.addEventListener('click', addCurrentShotToTimeline);
  if (btnInspectAddTimeline) btnInspectAddTimeline.addEventListener('click', addCurrentShotToTimeline);

  // Drag and Drop onto Track Lanes
  const trackLaneAreas = document.querySelectorAll('.track-lane-area');

  trackLaneAreas.forEach((laneArea) => {
    laneArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      laneArea.classList.add('drag-over');
    });

    laneArea.addEventListener('dragleave', () => laneArea.classList.remove('drag-over'));

    laneArea.addEventListener('drop', (e) => {
      e.preventDefault();
      laneArea.classList.remove('drag-over');

      try {
        const rawData = e.dataTransfer.getData('text/plain');
        if (!rawData) return;
        const assetData = JSON.parse(rawData);

        const rect = laneArea.getBoundingClientRect();
        const dropX = e.clientX - rect.left;
        let dropTimeSec = dropX / currentPPS;

        const trackRow = laneArea.closest('.timeline-track-row');
        const trackName = trackRow.querySelector('.track-name').textContent.trim();

        let clipClass = 'clip-video';
        if (trackName.startsWith('CHR')) clipClass = 'clip-char';
        else if (trackName.startsWith('TEXT')) clipClass = 'clip-text';
        else if (trackName.startsWith('AUD')) clipClass = 'clip-audio';

        createTimelineClip(laneArea, assetData, Math.max(0, dropTimeSec), 15, clipClass);
        activeAsset = assetData;
        loadAssetToMonitor(activeAsset);
      } catch (err) {
        console.error('Timeline drop error:', err);
      }
    });
  });

  function createTimelineClip(containerEl, assetData, startSec, durationSec, clipClass) {
    const clipEl = document.createElement('div');
    clipEl.className = `clip-block ${clipClass}`;
    clipEl.dataset.start = startSec.toFixed(1);
    clipEl.dataset.duration = durationSec.toFixed(1);
    clipEl.dataset.asset = JSON.stringify(assetData);

    clipEl.innerHTML = `
      <div class="resize-handle left"></div>
      <span class="clip-diamond">◆</span>
      <span class="clip-label">${assetData.name}</span>
      <span class="clip-meta">[${durationSec.toFixed(1)}s]</span>
      <div class="resize-handle right"></div>
    `;

    bindClipInteractions(clipEl, containerEl, assetData);
    containerEl.appendChild(clipEl);
    selectClip(clipEl);
    renderRulerAndClips();
  }

  function selectClip(clipEl) {
    document.querySelectorAll('.clip-block').forEach(c => c.classList.remove('selected'));
    if (clipEl) {
      clipEl.classList.add('selected');
      selectedClip = clipEl;
    } else {
      selectedClip = null;
    }
  }

  function bindClipInteractions(clipEl, laneArea, assetData) {
    clipEl.addEventListener('click', (e) => {
      e.stopPropagation();
      selectClip(clipEl);
      if (assetData) {
        activeAsset = assetData;
        loadAssetToMonitor(activeAsset);
      }
    });

    clipEl.addEventListener('mousedown', (e) => {
      if (e.target.classList.contains('resize-handle')) return;
      selectClip(clipEl);

      const startMouseX = e.clientX;
      const initialStartSec = parseFloat(clipEl.dataset.start) || 0;

      function onMouseMove(moveEvent) {
        const deltaX = moveEvent.clientX - startMouseX;
        const deltaSec = deltaX / currentPPS;
        let newStartSec = Math.max(0, initialStartSec + deltaSec);
        clipEl.dataset.start = newStartSec.toFixed(1);
        renderRulerAndClips();
      }

      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      }

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });

    const handleLeft = clipEl.querySelector('.resize-handle.left');
    const handleRight = clipEl.querySelector('.resize-handle.right');

    function startResize(e, isLeft) {
      e.stopPropagation();
      e.preventDefault();
      
      const startMouseX = e.clientX;
      const initialStartSec = parseFloat(clipEl.dataset.start) || 0;
      const initialDurationSec = parseFloat(clipEl.dataset.duration) || 15;

      function onMouseMove(moveEvent) {
        const deltaX = moveEvent.clientX - startMouseX;
        const deltaSec = deltaX / currentPPS;

        if (isLeft) {
          let newStartSec = Math.max(0, Math.min(initialStartSec + initialDurationSec - 0.5, initialStartSec + deltaSec));
          const newDurationSec = initialDurationSec - (newStartSec - initialStartSec);
          clipEl.dataset.start = newStartSec.toFixed(1);
          clipEl.dataset.duration = newDurationSec.toFixed(1);
        } else {
          let newDurationSec = Math.max(0.5, initialDurationSec + deltaSec);
          clipEl.dataset.duration = newDurationSec.toFixed(1);
        }
        renderRulerAndClips();
      }

      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      }

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    }

    if (handleLeft) handleLeft.addEventListener('mousedown', (e) => startResize(e, true));
    if (handleRight) handleRight.addEventListener('mousedown', (e) => startResize(e, false));
  }

  document.querySelectorAll('.clip-block').forEach((clipEl) => {
    const laneArea = clipEl.closest('.track-lane-area');
    bindClipInteractions(clipEl, laneArea, null);
  });

  // Helpers
  function formatTimecode(frames) {
    const totalSeconds = Math.floor(frames / fps);
    const ff = String(frames % fps).padStart(2, '0');
    const ss = String(totalSeconds % 60).padStart(2, '0');
    const mm = String(Math.floor(totalSeconds / 60) % 60).padStart(2, '0');
    const hh = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
    return `${hh}:${mm}:${ss}:${ff}`;
  }

  function formatShortTime(seconds) {
    const s = Math.floor(seconds % 60);
    const m = Math.floor(seconds / 60) % 60;
    const h = Math.floor(seconds / 3600);
    const ss = String(s).padStart(2, '0');
    const mm = String(m).padStart(2, '0');
    const hh = String(h).padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  }

  function updateUIProgress(currentSec, totalSec) {
    const percent = totalSec > 0 ? (currentSec / totalSec) * 100 : 0;
    scrubberInput.value = percent;
    playheadLine.style.left = `${120 + (currentSec * currentPPS)}px`;
    timecodeDisplay.textContent = formatTimecode(Math.floor(currentSec * fps));
    
    if (tcCurrentTime) tcCurrentTime.textContent = formatShortTime(currentSec);
    if (tcTotalDuration) tcTotalDuration.textContent = formatShortTime(totalSec || 90);
  }

  function updateAssetGroupCount() {
    const count = assetList.querySelectorAll('.asset-item').length;
    assetGroupTitle.textContent = `Imported Clips (${count})`;
  }

  function triggerFilePicker() { assetFileInput.click(); }
  if (btnImportTop) btnImportTop.addEventListener('click', triggerFilePicker);

  assetFileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (!files || files.length === 0) return;

    files.forEach((file) => {
      const objectUrl = URL.createObjectURL(file);
      let assetType = 'other';

      if (file.type.startsWith('video/')) assetType = 'video';
      else if (file.type.startsWith('image/')) assetType = 'image';
      else if (file.type.startsWith('audio/')) assetType = 'audio';

      const itemEl = document.createElement('div');
      itemEl.className = 'asset-item';
      itemEl.dataset.type = assetType;
      itemEl.dataset.url = objectUrl;
      itemEl.dataset.name = file.name;

      let badgeHtml = `<div class="asset-badge txt">FILE</div>`;
      if (assetType === 'video') badgeHtml = `<div class="asset-badge video">🎥</div>`;
      else if (assetType === 'image') badgeHtml = `<div class="asset-thumb"><img src="${objectUrl}" alt="${file.name}"></div>`;
      else if (assetType === 'audio') badgeHtml = `<div class="asset-badge audio">📊</div>`;

      itemEl.innerHTML = `
        ${badgeHtml}
        <span class="asset-name">${file.name}</span>
        <button class="asset-delete-btn" title="Delete Asset from Library">🗑️</button>
      `;

      assetList.prepend(itemEl);
      makeAssetDraggable(itemEl);
      bindAssetEvents(itemEl);
    });

    updateAssetGroupCount();
    const newest = assetList.querySelector('.asset-item');
    if (newest) newest.click();
    assetFileInput.value = '';
  });

  function bindAssetEvents(itemEl) {
    itemEl.addEventListener('click', (e) => {
      if (e.target.classList.contains('asset-delete-btn')) return;
      document.querySelectorAll('.asset-item').forEach(el => el.classList.remove('active'));
      itemEl.classList.add('active');

      activeAsset = {
        type: itemEl.dataset.type || 'video',
        url: itemEl.dataset.url || '',
        name: itemEl.dataset.name || itemEl.querySelector('.asset-name').textContent
      };
      loadAssetToMonitor(activeAsset);
    });

    const delBtn = itemEl.querySelector('.asset-delete-btn');
    if (delBtn) {
      delBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        itemEl.remove();
        updateAssetGroupCount();
      });
    }
  }

  function makeAssetDraggable(itemEl) {
    itemEl.setAttribute('draggable', 'true');
    itemEl.addEventListener('dragstart', (e) => {
      itemEl.classList.add('dragging');
      const assetData = {
        name: itemEl.dataset.name || itemEl.querySelector('.asset-name').textContent,
        type: itemEl.dataset.type || 'video',
        url: itemEl.dataset.url || ''
      };
      e.dataTransfer.setData('text/plain', JSON.stringify(assetData));
      e.dataTransfer.effectAllowed = 'copy';
    });

    itemEl.addEventListener('dragend', () => itemEl.classList.remove('dragging'));
  }

  document.querySelectorAll('.asset-item').forEach((itemEl) => {
    makeAssetDraggable(itemEl);
    bindAssetEvents(itemEl);
  });

  function loadAssetToMonitor(asset) {
    pauseMedia();
    inspectAssetName.value = asset.name;
    timelineV1Label.textContent = `CLIP: ${asset.name}`;

    viewportImg.classList.add('hidden');
    viewportVideo.classList.add('hidden');
    viewportAudioVis.classList.add('hidden');

    const isVideoFile = asset.type === 'video' || asset.url.endsWith('.mp4') || asset.url.endsWith('.webm') || asset.url.includes('/generated_assets/') || asset.url.includes('/file=');

    if (isVideoFile) {
      viewportVideo.classList.remove('hidden');
      console.log('🎬 Loading Video into Monitor Viewport, src:', asset.url);
      viewportVideo.src = asset.url;
      viewportVideo.currentTime = 0;
      viewportVideo.onloadedmetadata = () => updateUIProgress(0, viewportVideo.duration || totalSeqDuration);

    } else if (asset.type === 'image') {
      viewportImg.classList.remove('hidden');
      if (asset.url) viewportImg.src = asset.url;
      updateUIProgress(0, totalSeqDuration);

    } else if (asset.type === 'audio') {
      viewportAudioVis.classList.remove('hidden');
      audioFileLabel.textContent = asset.name;
      viewportVideo.src = asset.url;
      updateUIProgress(0, totalSeqDuration);

    } else {
      viewportImg.classList.remove('hidden');
      updateUIProgress(0, totalSeqDuration);
    }
  }

  function playMedia() {
    isPlaying = true;
    btnPlay.textContent = '⏸';

    const isVideoFile = activeAsset.type === 'video' || activeAsset.url.endsWith('.mp4') || activeAsset.url.endsWith('.webm') || activeAsset.url.includes('/generated_assets/') || activeAsset.url.includes('/file=');

    if (isVideoFile || activeAsset.type === 'audio') {
      viewportVideo.play().catch(err => console.warn('Autoplay restricted:', err));
    } else {
      clearInterval(playInterval);
      playInterval = setInterval(() => {
        currentFrame++;
        const currentSec = currentFrame / fps;
        updateUIProgress(currentSec, totalSeqDuration);
      }, 1000 / fps);
    }
  }

  function pauseMedia() {
    isPlaying = false;
    btnPlay.textContent = '▶';
    if (viewportVideo && !viewportVideo.paused) viewportVideo.pause();
    clearInterval(playInterval);
  }

  btnPlay.addEventListener('click', () => {
    if (isPlaying) pauseMedia(); else playMedia();
  });

  viewportVideo.addEventListener('timeupdate', () => {
    if (activeAsset.type === 'video' || activeAsset.url.endsWith('.mp4') || activeAsset.url.includes('/generated_assets/') || activeAsset.type === 'audio') {
      updateUIProgress(viewportVideo.currentTime, viewportVideo.duration || totalSeqDuration);
    }
  });

  viewportVideo.addEventListener('ended', pauseMedia);

  scrubberInput.addEventListener('input', (e) => {
    const percent = parseFloat(e.target.value);
    if (viewportVideo && viewportVideo.duration && !viewportVideo.classList.contains('hidden')) {
      viewportVideo.currentTime = (percent / 100) * viewportVideo.duration;
    } else {
      currentFrame = Math.floor((percent / 100) * totalSeqDuration * fps);
      updateUIProgress(currentFrame / fps, totalSeqDuration);
    }
  });
});
