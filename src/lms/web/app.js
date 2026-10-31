/**
 * Aethelgard Academy Web Platform Client
 * Production AI-led LMS / KMS frontend architecture.
 * Implements LearningFrame, ActivityRail, SplitPanes, and Concept Library KMS.
 */

const STATE = {
  activeView: "dashboard",
  activeUnitId: "PY-0.1",
  activeStep: "explain",
  currentUnit: null,
  units: [],
  concepts: [],
  ledger: [],
  recentSearches: [],
  playgroundOpen: true,
  railFolded: false,
  splitRatio: 0.5,
  stepStates: {
    explain: "now",
    predict: "not_yet",
    practice: "not_yet",
    verify: "not_yet",
    wrapup: "not_yet"
  },
  explanationCache: new Map(),
  isExplainingError: false,
  lastExecution: null
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", async () => {
  initMarkdownEngine();
  loadUserPreferences();
  loadRecentSearches();
  setupGlobalShortcuts();
  initSplitPanes();

  await loadUnitsCatalog();
  await loadLedgerEntries();
  await loadUnit(STATE.activeUnitId);
  updateDashboardCounts();

  // Initialize Concept Library Resting View
  renderConceptSearchResults([]);
  applyPlaygroundVisibility();
  applyRailFolded();
  renderActivityRail();
});

function loadUserPreferences() {
  try {
    const pg = localStorage.getItem("lms-playground-open");
    if (pg !== null) STATE.playgroundOpen = pg === "true";
    const rail = localStorage.getItem("lms-rail-folded");
    if (rail !== null) STATE.railFolded = rail === "true";
    const ratio = parseFloat(localStorage.getItem("lms-pane-ratio") || "0.5");
    if (!isNaN(ratio) && ratio >= 0.2 && ratio <= 0.8) STATE.splitRatio = ratio;
  } catch (err) {
    console.warn("Preferences storage unavailable", err);
  }
}

// --- Markdown Rendering Engine with GitHub Alerts & Prism ---
function initMarkdownEngine() {
  if (typeof marked !== "undefined") {
    marked.setOptions({
      gfm: true,
      breaks: true,
      headerIds: true,
      mangle: false
    });
  }
}

function processWikiLinks(text) {
  if (!text) return "";
  let res = text.replace(
    /\[\[([a-z0-9\-]+)\|([^\]]+)\]\]/gi,
    '<a class="wiki-link" onclick="openConceptDrawer(\'$1\')">$2</a>'
  );
  res = res.replace(
    /\[([^\]]+)\]\(concept:([a-z0-9\-]+)\)/gi,
    '<a class="wiki-link" onclick="openConceptDrawer(\'$2\')">$1</a>'
  );
  res = res.replace(/`input\(\)`/g, '<code class="wiki-link" onclick="openConceptDrawer(\'built-in-input\')">input()</code>');
  res = res.replace(/`print\(\)`/g, '<code class="wiki-link" onclick="openConceptDrawer(\'built-in-print\')">print()</code>');
  return res;
}

function renderProductionMarkdown(rawMarkdown) {
  if (!rawMarkdown) return "";

  // Normalize Windows CRLF to standard LF to prevent regex line matching failures
  const normalized = rawMarkdown.replace(/\r\n/g, "\n");

  // 1. Pre-process GitHub Alerts: > [!TIP], > [!NOTE], > [!WARNING], > [!IMPORTANT]
  let processed = normalized.replace(
    /^>\s*\[!(TIP|NOTE|WARNING|IMPORTANT|CAUTION)\][ \t]*(.*?)\n((?:>.*?(?:\n|$))*)/gim,
    (match, type, title, body) => {
      const cleanType = type.toUpperCase();
      const typeClass = cleanType.toLowerCase();
      const icon = cleanType === "TIP" ? "💡" : cleanType === "WARNING" ? "⚠️" : cleanType === "NOTE" ? "ℹ️" : "📌";
      const cleanTitle = processWikiLinks(title.trim() || cleanType);
      let cleanBody = body.replace(/^>[ \t]?/gm, "").trim();
      cleanBody = processWikiLinks(cleanBody);
      const parsedBody = typeof marked !== "undefined" ? marked.parse(cleanBody) : cleanBody;
      return `<div class="callout-alert callout-${typeClass}"><div class="callout-alert-title"><span>${icon}</span> <span>${cleanTitle}</span></div><div class="callout-alert-content">${parsedBody}</div></div>\n\n`;
    }
  );

  // 2. Process remaining Wiki links across main text
  processed = processWikiLinks(processed);

  // 3. Parse via Marked.js
  let html = typeof marked !== "undefined" ? marked.parse(processed) : processed;

  return html;
}

function highlightSyntaxWithin(element) {
  if (typeof Prism !== "undefined" && element) {
    Prism.highlightAllUnder(element);
  }
  attachCodeBlockActions(element);
}

// Attach "Open in Playground" action header to code blocks in reading pane
function attachCodeBlockActions(container) {
  if (!container) return;
  const preElements = container.querySelectorAll("pre");
  preElements.forEach(pre => {
    if (pre.parentElement && pre.parentElement.classList.contains("code-block-wrapper")) return;
    const wrapper = document.createElement("div");
    wrapper.className = "code-block-wrapper";
    
    const header = document.createElement("div");
    header.className = "code-block-header";
    header.innerHTML = `
      <span class="code-lang">Python</span>
      <button type="button" class="btn-snippet-copy" onclick="copySnippetToPlayground(this)">
        ⚡ Open in Playground
      </button>
    `;
    
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(header);
    wrapper.appendChild(pre);
  });
}

function copySnippetToPlayground(button) {
  const wrapper = button.closest(".code-block-wrapper");
  if (!wrapper) return;
  const codeEl = wrapper.querySelector("code");
  if (!codeEl) return;
  const codeText = codeEl.innerText.trim();

  const editor = document.getElementById("studio-editor");
  if (editor) {
    editor.value = codeText;
    updateLineNumbers();
    if (!STATE.playgroundOpen) {
      togglePlayground();
    }
    editor.classList.add("editor-flash");
    setTimeout(() => editor.classList.remove("editor-flash"), 600);
    showToast("Snippet loaded into Playground Editor");
  }
}

// --- SplitPanes with Draggable Divider ---
function initSplitPanes() {
  const divider = document.getElementById("studio-split-divider");
  const container = document.getElementById("studio-workarea");
  const leftPane = document.getElementById("studio-instruction-pane");
  if (!divider || !container || !leftPane) return;

  applyPaneRatio(STATE.splitRatio);

  let isDragging = false;

  divider.addEventListener("mousedown", (e) => {
    e.preventDefault();
    isDragging = true;
    document.body.classList.add("resizing-panes");
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const ratio = Math.max(0.25, Math.min(0.75, x / rect.width));
    applyPaneRatio(ratio);
  });

  const stopDrag = () => {
    if (isDragging) {
      isDragging = false;
      document.body.classList.remove("resizing-panes");
    }
  };

  window.addEventListener("mouseup", stopDrag);
  window.addEventListener("mouseleave", stopDrag);

  divider.addEventListener("dblclick", () => {
    applyPaneRatio(0.5);
  });

  divider.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      e.preventDefault();
      const current = STATE.splitRatio;
      const delta = e.key === "ArrowRight" ? 0.05 : -0.05;
      const next = Math.max(0.25, Math.min(0.75, current + delta));
      applyPaneRatio(next);
    }
  });
}

function applyPaneRatio(ratio) {
  STATE.splitRatio = ratio;
  const container = document.getElementById("studio-workarea");
  const leftPane = document.getElementById("studio-instruction-pane");
  if (!container || !leftPane) return;
  const pct = Math.round(ratio * 100);
  leftPane.style.flex = `0 0 ${pct}%`;
  container.dataset.ratio = ratio.toString();
  try {
    localStorage.setItem("lms-pane-ratio", ratio.toString());
  } catch (err) {}
}

// --- Toggleable Playground ---
function togglePlayground() {
  STATE.playgroundOpen = !STATE.playgroundOpen;
  applyPlaygroundVisibility();
  try {
    localStorage.setItem("lms-playground-open", STATE.playgroundOpen.toString());
  } catch (err) {}
}

function applyPlaygroundVisibility() {
  const workarea = document.getElementById("studio-workarea");
  const toggleBtn = document.getElementById("btn-toggle-playground");
  const divider = document.getElementById("studio-split-divider");
  const playgroundPane = document.getElementById("studio-playground-pane");

  if (!workarea) return;

  if (STATE.playgroundOpen) {
    workarea.classList.remove("playground-collapsed");
    if (toggleBtn) {
      toggleBtn.innerHTML = `<span>⚡</span> Playground: <strong>On</strong>`;
      toggleBtn.classList.add("active");
      toggleBtn.setAttribute("aria-pressed", "true");
    }
    if (divider) divider.style.display = "flex";
    if (playgroundPane) playgroundPane.style.display = "flex";
  } else {
    workarea.classList.add("playground-collapsed");
    if (toggleBtn) {
      toggleBtn.innerHTML = `<span>⚡</span> Playground: <strong>Off</strong>`;
      toggleBtn.classList.remove("active");
      toggleBtn.setAttribute("aria-pressed", "false");
    }
    if (divider) divider.style.display = "none";
    if (playgroundPane) playgroundPane.style.display = "none";
  }
}

// --- Collapsible Activity Rail ---
function toggleActivityRail() {
  STATE.railFolded = !STATE.railFolded;
  applyRailFolded();
  try {
    localStorage.setItem("lms-rail-folded", STATE.railFolded.toString());
  } catch (err) {}
}

function applyRailFolded() {
  const rail = document.getElementById("studio-activity-rail");
  const toggleBtn = document.getElementById("btn-toggle-rail");
  if (!rail) return;

  if (STATE.railFolded) {
    rail.classList.add("folded");
    if (toggleBtn) {
      toggleBtn.innerHTML = "➔";
      toggleBtn.setAttribute("title", "Expand activities rail");
    }
  } else {
    rail.classList.remove("folded");
    if (toggleBtn) {
      toggleBtn.innerHTML = "←";
      toggleBtn.setAttribute("title", "Collapse activities rail");
    }
  }
}

function renderActivityRail() {
  const activities = [
    { id: "explain", label: "1. Explain (Notes & Video)", icon: "📖" },
    { id: "predict", label: "2. Predict (Invariant)", icon: "🎯" },
    { id: "practice", label: "3. Practice (Editor)", icon: "💻" },
    { id: "verify", label: "4. Debug & Verify", icon: "✓" },
    { id: "wrapup", label: "5. Wrapup & Evidence", icon: "📜" }
  ];

  const listEl = document.getElementById("rail-activities-list");
  if (!listEl) return;

  listEl.innerHTML = activities.map(act => {
    const status = STATE.stepStates[act.id] || "not_yet";
    const isCurrent = STATE.activeStep === act.id;
    const mark = isCurrent ? "●" : (status === "done" ? "✓" : "○");
    const activeClass = isCurrent ? "active" : "";
    const doneClass = status === "done" ? "done" : "";
    const locked = status === "not_yet" && !isCurrent;

    return `
      <li>
        <button type="button" class="rail-step ${activeClass} ${doneClass}" 
                title="${act.label} (${isCurrent ? 'Current' : (status === 'done' ? 'Completed' : 'Upcoming')})"
                onclick="goToStep('${act.id}')">
          <span class="rail-icon">${mark}</span>
          <span class="rail-label">${act.label}</span>
        </button>
      </li>
    `;
  }).join("");
}

// --- View Switching ---
function showView(viewName) {
  STATE.activeView = viewName;
  const views = ["dashboard", "roadmap", "unit-studio", "concept-library", "ledger"];
  
  views.forEach(v => {
    const panel = document.getElementById(`view-${v}`);
    const navBtn = document.getElementById(`nav-btn-${v}`);
    if (v === viewName) {
      if (panel) panel.classList.add("active");
      if (navBtn) navBtn.classList.add("active");
    } else {
      if (panel) panel.classList.remove("active");
      if (navBtn) navBtn.classList.remove("active");
    }
  });

  if (viewName === "roadmap") renderRoadmap();
  if (viewName === "concept-library") {
    const input = document.getElementById("concept-search-input");
    renderRecentSearches();
    if (input && input.value.trim()) {
      handleConceptSearchInput(input.value);
    } else {
      renderConceptSearchResults([]);
    }
  }
  if (viewName === "ledger") loadLedgerEntries();
}

function resumeActiveUnit() {
  showView("unit-studio");
  loadUnit(STATE.activeUnitId);
}

// --- Stepper Navigation in Unit Studio ---
function goToStep(stepName) {
  STATE.activeStep = stepName;
  const steps = ["explain", "predict", "practice", "verify", "wrapup"];
  
  steps.forEach(s => {
    const panel = document.getElementById(`phase-${s}`);
    if (panel) {
      panel.style.display = (s === stepName) ? "flex" : "none";
    }
  });

  // Automatically ensure playground is open for coding steps
  if ((stepName === "practice" || stepName === "verify") && !STATE.playgroundOpen) {
    togglePlayground();
  }

  renderActivityRail();
}

// --- Catalog & Unit Loading ---
async function loadUnitsCatalog() {
  try {
    const res = await fetch("/api/v1/units?course_id=python");
    if (res.ok) {
      STATE.units = await res.json();
    }
  } catch (err) {
    console.error("Failed to fetch units:", err);
  }
}

async function loadUnit(unitId) {
  STATE.activeUnitId = unitId;
  const select = document.getElementById("studio-unit-select");
  if (select && select.value !== unitId) select.value = unitId;

  // Reset step states for newly loaded unit
  STATE.stepStates = {
    explain: "now",
    predict: "not_yet",
    practice: "not_yet",
    verify: "not_yet",
    wrapup: "not_yet"
  };

  try {
    const res = await fetch(`/api/v1/units/${unitId}`);
    if (!res.ok) throw new Error("Unit not found");
    const unit = await res.json();
    STATE.currentUnit = unit;

    // Update Topbar Breadcrumb & Badges
    const breadcrumbEl = document.getElementById("studio-breadcrumb");
    if (breadcrumbEl) {
      breadcrumbEl.innerHTML = `<span>Python Track</span> <span>›</span> <span>Stage 0</span> <span>›</span> <strong>${unit.unit_id}: ${unit.title}</strong>`;
    }

    const skillsContainer = document.getElementById("unit-target-skills");
    if (skillsContainer && unit.target_skills) {
      skillsContainer.innerHTML = unit.target_skills.map(s => 
        `<span class="skill-chip">${s.skill_id} (${s.goal_level})</span>`
      ).join("");
    }

    // Render Lesson Markdown with Production Engine
    const explainBody = document.getElementById("explain-content");
    const explainUnitId = document.getElementById("explain-unit-id");
    if (explainUnitId) explainUnitId.innerText = unit.unit_id;
    if (explainBody) {
      explainBody.innerHTML = renderProductionMarkdown(unit.lesson_markdown || unit.concept_line);
      highlightSyntaxWithin(explainBody);
    }

    // Render Video Walkthrough Timestamps
    const tsContainer = document.getElementById("video-timestamps");
    if (tsContainer) {
      if (unit.media && unit.media.length > 0 && unit.media[0].timestamps) {
        tsContainer.innerHTML = unit.media[0].timestamps.map(t => 
          `<div class="timestamp-row">
            <span class="ts-topic">${t.topic}</span>
            <span class="ts-time">${t.time}</span>
          </div>`
        ).join("");
      } else {
        tsContainer.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem;">No timestamp anchors available.</div>`;
      }
    }

    // Render Starter Code
    const editor = document.getElementById("studio-editor");
    if (editor) {
      editor.value = unit.starter_code || `# Unit ${unit.unit_id}: ${unit.title}\n# Write your solution below:\n`;
      updateLineNumbers();
    }

    const badge = document.getElementById("practice-unit-badge");
    if (badge) badge.innerText = unit.unit_id;

    goToStep("explain");
  } catch (err) {
    console.error("Failed to load unit details:", err);
  }
}

// --- CO-6 Concept Explanation Submission ---
async function submitConceptExplanation() {
  const input = document.getElementById("co6-input");
  const feedback = document.getElementById("co6-eval-feedback");
  if (!input) return;

  const text = input.value.trim();
  if (text.length < 5) {
    feedback.innerHTML = `<span style="color: var(--color-danger); font-weight: 600;">Please provide an explanation before proceeding.</span>`;
    return;
  }

  feedback.innerHTML = `<span style="color: var(--text-muted);">Evaluating mental model...</span>`;

  try {
    const res = await fetch("/api/v1/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        unit_id: STATE.activeUnitId,
        explanation: text,
        learner_id: "default_learner"
      })
    });

    if (res.ok) {
      const data = await res.json();
      const isSolid = data.status === "Solid";
      feedback.innerHTML = isSolid 
        ? `<span style="color: var(--color-success); font-weight: 700;">✓ Mental Model: Solid! Advancing to Activity 2...</span>`
        : `<span style="color: var(--color-warning); font-weight: 700;">⚠ Mental Model: Shaky (${data.feedback}). Proceeding to practice...</span>`;
      
      STATE.stepStates.explain = "done";
      STATE.stepStates.predict = "now";
      renderActivityRail();

      await loadLedgerEntries();
      updateDashboardCounts();
      setTimeout(() => goToStep("predict"), 800);
    }
  } catch (err) {
    feedback.innerHTML = `<span style="color: var(--color-danger);">Evaluation failed: ${err.message}</span>`;
  }
}

function commitPrediction() {
  const selected = document.querySelector('input[name="pred-opt"]:checked');
  if (!selected) {
    alert("Please select an option to commit your prediction.");
    return;
  }
  STATE.stepStates.predict = "done";
  STATE.stepStates.practice = "now";
  renderActivityRail();
  goToStep("practice");
  showToast("Prediction committed. Playground opened!");
}

// --- Interactive Execution in Playground ---
function executePlaygroundCode() {
  const code = document.getElementById("studio-editor").value;
  const terminal = document.getElementById("terminal-screen");
  const promptBox = document.getElementById("terminal-prompt-box");
  const stdinField = document.getElementById("stdin-field");
  const status = document.getElementById("execution-status");
  const errorBox = document.getElementById("error-explanation-box");

  if (errorBox) errorBox.style.display = "none";
  status.innerText = "Running...";

  if (code.includes("input(")) {
    terminal.innerHTML = `
      <div class="term-line-meta">$ python solution.py</div>
      <div class="term-line-warn">⏳ Program paused: waiting for interactive terminal input...</div>
    `;
    if (promptBox) promptBox.style.display = "flex";
    if (stdinField) {
      stdinField.value = "";
      stdinField.focus();
    }
    status.innerText = "Paused on stdin";
  } else {
    runSandboxExecution(code, "");
  }
}

function handleStdinEnter(event) {
  if (event.key === "Enter") {
    const stdinVal = document.getElementById("stdin-field").value;
    const promptBox = document.getElementById("terminal-prompt-box");
    if (promptBox) promptBox.style.display = "none";
    
    const code = document.getElementById("studio-editor").value;
    runSandboxExecution(code, stdinVal);
  }
}

async function runSandboxExecution(code, stdinInput) {
  const terminal = document.getElementById("terminal-screen");
  const status = document.getElementById("execution-status");
  const errorBox = document.getElementById("error-explanation-box");

  try {
    const res = await fetch("/api/v1/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: code,
        stdin_input: stdinInput ? `${stdinInput}\n` : null,
        timeout_seconds: 5.0
      })
    });

    if (res.ok) {
      const result = await res.json();
      STATE.lastExecution = { code, result };
      status.innerText = result.success ? "Exit Code 0" : "Execution Error";

      let outputHtml = `<div class="term-line-meta">$ python solution.py</div>`;
      if (stdinInput) {
        outputHtml += `<div class="term-line-input">Input supplied: <strong style="color: #ffffff;">${escapeHtml(stdinInput)}</strong></div>`;
      }
      if (result.stdout) {
        outputHtml += `<div class="term-line-out">${escapeHtml(result.stdout)}</div>`;
      }
      if (result.stderr) {
        outputHtml += `<div class="term-line-err">${escapeHtml(result.stderr)}</div>`;
        if (errorBox) {
          errorBox.style.display = "block";
          document.getElementById("error-text-display").innerText = result.stderr.trim().split("\n").slice(-2).join("\n");
        }
      }
      outputHtml += `<div class="term-line-meta">[Process finished in ${result.duration_ms}ms with exit code ${result.exit_code}]</div>`;
      terminal.innerHTML = outputHtml;
    }
  } catch (err) {
    status.innerText = "Runner Error";
    terminal.innerHTML += `<div class="term-line-err">Failed to connect to execution runner: ${err.message}</div>`;
  }
}

// Socratic AI Error Explanation with Cache and Lock
async function explainCurrentError() {
  if (STATE.isExplainingError || !STATE.lastExecution) return;
  const btn = document.getElementById("btn-explain-error");
  const diagContainer = document.getElementById("error-diag-container");
  if (!btn || !diagContainer) return;

  const code = STATE.lastExecution.code;
  const stderr = STATE.lastExecution.result.stderr || "";

  // Check cache to prevent duplicate tokens / slow requests
  const cacheKey = JSON.stringify({ code, stderr });
  if (STATE.explanationCache.has(cacheKey)) {
    const cached = STATE.explanationCache.get(cacheKey);
    diagContainer.innerHTML = `<div class="socratic-advice">${renderProductionMarkdown(cached)}</div>`;
    diagContainer.style.display = "block";
    return;
  }

  STATE.isExplainingError = true;
  btn.disabled = true;
  btn.innerText = "Explaining error with AXIS AI...";
  diagContainer.style.display = "block";
  diagContainer.innerHTML = `<div style="color: var(--text-muted); font-size: 0.825rem;"><span>⏳</span> Consulting AXIS Socratic Mentor...</div>`;

  try {
    const res = await fetch("/api/v1/explain-error", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        unit_id: STATE.activeUnitId,
        code: code,
        error: stderr,
        learner_id: "default_learner"
      })
    });

    if (res.ok) {
      const data = await res.json();
      const reply = data.explanation || "Inspect the line numbers shown in the traceback and verify your syntax.";
      STATE.explanationCache.set(cacheKey, reply);
      diagContainer.innerHTML = `<div class="socratic-advice">${renderProductionMarkdown(reply)}</div>`;
    } else {
      diagContainer.innerHTML = `<div style="color: var(--color-warning);">Diagnostic unavailable: Socratic companion offline.</div>`;
    }
  } catch (err) {
    diagContainer.innerHTML = `<div style="color: var(--color-danger);">Error requesting explanation: ${err.message}</div>`;
  } finally {
    STATE.isExplainingError = false;
    btn.disabled = false;
    btn.innerText = "💡 Explain this error with AXIS AI";
  }
}

async function verifyPlaygroundSolution() {
  const code = document.getElementById("studio-editor").value;
  const terminal = document.getElementById("terminal-screen");
  const status = document.getElementById("execution-status");

  if (!STATE.currentUnit) {
    alert("No test suite available for this unit.");
    return;
  }

  status.innerText = "Verifying assertions...";

  try {
    const res = await fetch(`/api/v1/learners/me/units/${STATE.activeUnitId}/playground:verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: code })
    });

    if (res.ok) {
      const result = await res.json();
      if (result.success) {
        status.innerText = "Verified PASS";
        terminal.innerHTML = `
          <div class="term-line-meta">$ uv run pytest test_solution.py</div>
          <div class="term-line-pass">✓ ALL SYSTEM BOUNDARY ASSERTIONS PASSED (${result.duration_ms}ms)</div>
          <div style="color: #e2e8f0; margin-block-start: 0.5rem;">Evidence Ledger record appended: Strong (None).</div>
          <div style="color: #a7f3d0;">Progression updated: ${STATE.activeUnitId} Completed.</div>
        `;

        await fetch(`/api/v1/learners/default_learner/progress`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ unit_id: STATE.activeUnitId, status: "Completed" })
        });

        STATE.stepStates.practice = "done";
        STATE.stepStates.verify = "done";
        STATE.stepStates.wrapup = "now";
        renderActivityRail();

        await loadLedgerEntries();
        updateDashboardCounts();
        showToast("Exercise verified! Evidence logged to Ledger.");
        setTimeout(() => goToStep("wrapup"), 900);
      } else {
        status.innerText = "Verification Failed";
        terminal.innerHTML = `
          <div class="term-line-meta">$ uv run pytest test_solution.py</div>
          <div class="term-line-err">✗ VERIFICATION FAILED:</div>
          <div class="term-line-err" style="white-space: pre-wrap;">${escapeHtml(result.stderr || result.stdout)}</div>
        `;
      }
    }
  } catch (err) {
    status.innerText = "Verify Error";
    terminal.innerHTML += `<div class="term-line-err">Verification request failed: ${err.message}</div>`;
  }
}

function clearTerminalScreen() {
  const terminal = document.getElementById("terminal-screen");
  if (terminal) terminal.innerHTML = `<div class="term-line-meta">$ Terminal cleared. Click 'Run Code' or 'Verify Solution'.</div>`;
}

function updateLineNumbers() {
  const editor = document.getElementById("studio-editor");
  const lineNumbers = document.getElementById("studio-line-numbers");
  if (!editor || !lineNumbers) return;
  const count = editor.value.split("\n").length;
  lineNumbers.innerHTML = Array.from({length: Math.max(count, 14)}, (_, i) => i + 1).join("<br>");
}

function resetCurrentCode() {
  if (STATE.currentUnit && STATE.currentUnit.starter_code) {
    const editor = document.getElementById("studio-editor");
    if (editor) {
      editor.value = STATE.currentUnit.starter_code;
      updateLineNumbers();
      showToast("Starter code restored");
    }
  }
}

// --- Roadmap Rendering (Python MoC) ---
function renderRoadmap() {
  const container0 = document.getElementById("roadmap-stage-0");
  const container1 = document.getElementById("roadmap-stage-1");
  if (!container0 || !container1) return;

  const stage0Units = STATE.units.filter(u => u.stage === 0);
  const stage1Units = STATE.units.filter(u => u.stage === 1);

  container0.innerHTML = stage0Units.map(u => `
    <div class="card card-hover" onclick="loadUnit('${u.unit_id}'); showView('unit-studio');">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-block-end: 0.35rem;">
        <span style="font-family: var(--font-mono); font-weight: 800; color: var(--color-primary);">${u.unit_id}</span>
        <span class="status-badge status-ready">READY</span>
      </div>
      <div style="font-weight: 700; font-size: 0.95rem; margin-block-end: 0.25rem;">${u.title}</div>
      <p style="font-size: 0.8rem; color: var(--text-muted); margin-block-end: 0.75rem;">${u.concept_line}</p>
      <div style="display: flex; gap: 0.35rem; flex-wrap: wrap;">
        ${u.target_skills.map(s => `<span class="skill-chip">${s.skill_id}</span>`).join("")}
      </div>
    </div>
  `).join("");

  container1.innerHTML = stage1Units.map(u => `
    <div class="card" style="opacity: 0.75;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-block-end: 0.35rem;">
        <span style="font-family: var(--font-mono); font-weight: 800; color: var(--text-muted);">${u.unit_id}</span>
        <span class="status-badge" style="background: var(--bg-surface); color: var(--text-muted);">STAGE 1</span>
      </div>
      <div style="font-weight: 700; font-size: 0.95rem; margin-block-end: 0.25rem;">${u.title}</div>
      <p style="font-size: 0.8rem; color: var(--text-muted);">${u.concept_line}</p>
    </div>
  `).join("");
}

// ==============================================================
// CONCEPT LIBRARY KMS (SURFACED ONLY UPON SEARCH OR WIKI LINK)
// ==============================================================

function loadRecentSearches() {
  try {
    const raw = localStorage.getItem("aethelgard_recent_searches");
    STATE.recentSearches = raw ? JSON.parse(raw) : ["input()", "print()", "sequential execution", "variables"];
  } catch {
    STATE.recentSearches = ["input()", "print()", "sequential execution", "variables"];
  }
}

function saveRecentSearch(term) {
  if (!term || term.trim().length < 2) return;
  const clean = term.trim();
  STATE.recentSearches = [clean, ...STATE.recentSearches.filter(s => s.toLowerCase() !== clean.toLowerCase())].slice(0, 5);
  try {
    localStorage.setItem("aethelgard_recent_searches", JSON.stringify(STATE.recentSearches));
  } catch {}
  renderRecentSearches();
}

function clearRecentSearches() {
  STATE.recentSearches = [];
  try { localStorage.removeItem("aethelgard_recent_searches"); } catch {}
  renderRecentSearches();
}

function renderRecentSearches() {
  const row = document.getElementById("recent-searches-row");
  if (!row) return;

  if (STATE.recentSearches.length === 0) {
    row.innerHTML = `<span style="color: var(--text-muted); font-size: 0.75rem;">No recent searches.</span>`;
    return;
  }

  const pillsHtml = STATE.recentSearches.map(term => 
    `<button class="recent-pill" onclick="applyRecentSearch('${escapeHtml(term)}')">
      <span>🔎</span> ${escapeHtml(term)}
    </button>`
  ).join("");

  row.innerHTML = `
    <span style="color: var(--text-muted); font-size: 0.75rem; font-weight: 600;">Recent:</span>
    ${pillsHtml}
    <button onclick="clearRecentSearches()" class="clear-pills-btn">Clear</button>
  `;
}

function applyRecentSearch(term) {
  const input = document.getElementById("concept-search-input");
  if (input) {
    input.value = term;
    handleConceptSearchInput(term);
  }
}

let searchDebounceTimer = null;
function handleConceptSearchInput(query) {
  clearTimeout(searchDebounceTimer);
  const q = query.trim();

  if (!q) {
    renderConceptSearchResults([]);
    return;
  }

  searchDebounceTimer = setTimeout(async () => {
    saveRecentSearch(q);
    try {
      const res = await fetch(`/api/v1/concepts?search=${encodeURIComponent(q)}`);
      if (res.ok) {
        const results = await res.json();
        renderConceptSearchResults(results, q);
      }
    } catch (err) {
      console.error("Search failed:", err);
    }
  }, 200);
}

function renderConceptSearchResults(results, query = "") {
  const container = document.getElementById("concept-results-container");
  if (!container) return;

  // Resting State: No search performed
  if (!query && results.length === 0) {
    container.innerHTML = `
      <div class="card" style="text-align: center; padding: 3rem 1.5rem; background: var(--bg-card); border-style: dashed;">
        <div style="font-size: 2.25rem; margin-block-end: 0.5rem;">📚</div>
        <h3 style="font-size: 1.1rem; font-weight: 700; margin-block-end: 0.35rem;">Concept Library Database (Resting Mode)</h3>
        <p style="color: var(--text-muted); font-size: 0.85rem; max-inline-size: 520px; margin-inline: auto;">
          Concepts are stored in the database as markdown notes and surface <strong>only when searched or clicked via wiki link</strong> in your lesson notes.
        </p>
        <div style="margin-block-start: 1rem; display: flex; justify-content: center; gap: 0.5rem;">
          <button onclick="applyRecentSearch('input()')" class="btn">Try "input()"</button>
          <button onclick="applyRecentSearch('sequential execution')" class="btn">Try "sequential execution"</button>
        </div>
      </div>
    `;
    return;
  }

  // No Results State
  if (results.length === 0) {
    container.innerHTML = `
      <div class="card" style="text-align: center; padding: 2.5rem 1rem;">
        <div style="font-size: 1.5rem; color: var(--color-warning); margin-block-end: 0.5rem;">🔍</div>
        <div style="font-weight: 700; font-size: 0.95rem;">No concept notes matched "${escapeHtml(query)}"</div>
        <p style="color: var(--text-muted); font-size: 0.825rem; margin-block-start: 0.25rem;">
          Try searching for built-ins (<code>input</code>, <code>print</code>), variables, sequential execution, or f-strings.
        </p>
      </div>
    `;
    return;
  }

  // Active Results Grid
  container.innerHTML = `
    <div style="margin-block-end: 0.75rem; font-size: 0.8rem; color: var(--text-muted);">
      Found <strong>${results.length}</strong> concept note${results.length > 1 ? 's' : ''} matching "<strong>${escapeHtml(query)}</strong>":
    </div>
    <div class="grid-3">
      ${results.map(c => `
        <div class="card card-hover" style="display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-block-end: 0.35rem;">
              <span style="font-size: 0.725rem; text-transform: uppercase; color: var(--color-primary); font-weight: 700; letter-spacing: 0.05em;">${c.category}</span>
              <span style="font-size: 0.725rem; color: var(--text-muted); font-family: var(--font-mono);">${c.concept_id}</span>
            </div>
            <div style="font-weight: 800; font-size: 1rem; margin-block-end: 0.35rem; color: var(--text-main);">${c.name}</div>
            <p style="font-size: 0.825rem; color: var(--text-muted); margin-block-end: 0.75rem; line-height: 1.5;">${c.summary}</p>
          </div>
          <div>
            <div style="display: flex; gap: 0.5rem; margin-block-start: 0.5rem;">
              <button onclick="openConceptDrawer('${c.concept_id}')" class="btn btn-primary" style="flex: 1; justify-content: center; font-size: 0.75rem;">
                Read Full Markdown Note ➔
              </button>
            </div>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

// --- Slide-Over Drawer for Concept Markdown Notes ---
async function openConceptDrawer(conceptId) {
  try {
    const res = await fetch(`/api/v1/concepts/${conceptId}`);
    if (!res.ok) throw new Error("Concept note not found");
    const concept = await res.json();

    document.getElementById("drawer-title").innerText = concept.name;
    document.getElementById("drawer-category").innerText = concept.category;
    
    const docLink = document.getElementById("drawer-doc-link");
    if (docLink) {
      docLink.href = concept.doc_url || "#";
      docLink.style.display = concept.doc_url ? "inline-flex" : "none";
    }

    const contentBox = document.getElementById("drawer-content");
    if (contentBox) {
      contentBox.innerHTML = renderProductionMarkdown(concept.content_markdown || concept.summary);
      highlightSyntaxWithin(contentBox);
    }

    const drawer = document.getElementById("concept-drawer");
    const backdrop = document.getElementById("drawer-backdrop");
    if (drawer) drawer.classList.add("active");
    if (backdrop) backdrop.classList.add("active");

    saveRecentSearch(concept.name);
  } catch (err) {
    alert("Could not open concept note: " + err.message);
  }
}

function closeConceptDrawer() {
  const drawer = document.getElementById("concept-drawer");
  const backdrop = document.getElementById("drawer-backdrop");
  if (drawer) drawer.classList.remove("active");
  if (backdrop) backdrop.classList.remove("active");
}

// --- Evidence Ledger ---
async function loadLedgerEntries() {
  try {
    const res = await fetch("/api/v1/learners/default_learner/ledger");
    if (res.ok) {
      STATE.ledger = await res.json();
      renderLedgerTable();
      updateDashboardCounts();
    }
  } catch (err) {
    console.error("Failed to load evidence ledger:", err);
  }
}

function renderLedgerTable() {
  const tbody = document.getElementById("ledger-table-body");
  if (!tbody) return;

  if (STATE.ledger.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="padding: 1.5rem; text-align: center; color: var(--text-muted);">No evidence recorded yet. Verify an exercise in Unit Studio!</td></tr>`;
    return;
  }

  tbody.innerHTML = STATE.ledger.map(entry => `
    <tr style="border-block-end: 1px solid var(--border-color);">
      <td style="padding: 0.75rem 1rem; font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">${formatDate(entry.recorded_at)}</td>
      <td style="padding: 0.75rem 1rem; font-family: var(--font-mono); font-weight: 700;">${entry.unit_id}</td>
      <td style="padding: 0.75rem 1rem;"><span style="font-family: var(--font-mono); font-weight: 700; color: var(--color-primary);">${entry.skill_id}</span></td>
      <td style="padding: 0.75rem 1rem;">${entry.evidence_category}</td>
      <td style="padding: 0.75rem 1rem;"><span style="color: var(--color-success); font-weight: 700;">${entry.evidence_strength}</span></td>
      <td style="padding: 0.75rem 1rem; color: var(--text-muted);">${escapeHtml(entry.observed_reasoning || entry.demonstration_context)}</td>
    </tr>
  `).join("");
}

function updateDashboardCounts() {
  const ledgerEl = document.getElementById("dash-ledger-count");
  if (ledgerEl) ledgerEl.innerText = `${STATE.ledger.length} Verified Entries`;
}

// --- Keyboard Shortcuts ---
function setupGlobalShortcuts() {
  document.addEventListener("keydown", e => {
    // Ctrl+K / Cmd+K focuses concept search
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      showView("concept-library");
      const search = document.getElementById("concept-search-input");
      if (search) search.focus();
    }
    // Ctrl+Enter runs playground code
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && STATE.activeView === "unit-studio") {
      e.preventDefault();
      executePlaygroundCode();
    }
    // Escape closes drawer
    if (e.key === "Escape") {
      closeConceptDrawer();
    }
  });
}

// --- Notification Toast ---
function showToast(message) {
  let toast = document.getElementById("lms-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "lms-toast";
    toast.className = "toast-message";
    document.body.appendChild(toast);
  }
  toast.innerText = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
}

// --- Helpers ---
function toggleModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  if (modal.open) modal.close(); else modal.showModal();
}

function escapeHtml(text) {
  if (!text) return "";
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function formatDate(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    return d.toISOString().replace("T", " ").substring(0, 19);
  } catch {
    return isoStr;
  }
}
