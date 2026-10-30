/**
 * Aethelgard Academy Web Platform Client
 * Production AI-led LMS / KMS frontend architecture.
 */

const STATE = {
  activeView: "dashboard",
  activeUnitId: "PY-0.1",
  activeStep: "explain",
  currentUnit: null,
  units: [],
  concepts: [],
  ledger: [],
  recentSearches: []
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", async () => {
  initMarkdownEngine();
  loadRecentSearches();
  setupGlobalShortcuts();

  await loadUnitsCatalog();
  await loadLedgerEntries();
  await loadUnit(STATE.activeUnitId);
  updateDashboardCounts();

  // Initialize Concept Library Resting View
  renderConceptSearchResults([]);
});

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

  // 1. Pre-process GitHub Alerts: > [!TIP], > [!NOTE], > [!WARNING], > [!IMPORTANT]
  let processed = rawMarkdown.replace(
    /^>\s*\[!(TIP|NOTE|WARNING|IMPORTANT|CAUTION)\][ \t]*(.*?)\n((?:>.*?(?:\n|$))*)/gim,
    (match, type, title, body) => {
      const cleanType = type.toUpperCase();
      const typeClass = cleanType.toLowerCase();
      const icon = cleanType === "TIP" ? "💡" : cleanType === "WARNING" ? "⚠️" : cleanType === "NOTE" ? "ℹ️" : "📌";
      const cleanTitle = processWikiLinks(title.trim() || cleanType);
      let cleanBody = body.replace(/^>\s?/gm, "").trim();
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
  const steps = ["explain", "predict", "practice"];
  
  steps.forEach(s => {
    const btn = document.getElementById(`step-btn-${s}`);
    const panel = document.getElementById(`phase-${s}`);
    if (s === stepName) {
      if (btn) btn.classList.add("active");
      if (panel) panel.style.display = (s === "practice" ? "grid" : (s === "explain" ? "grid" : "flex"));
    } else {
      if (btn) btn.classList.remove("active");
      if (panel) panel.style.display = "none";
    }
  });
}

// --- Catalog & Unit Loading ---
async function loadUnitsCatalog() {
  try {
    const res = await fetch("/api/v1/units");
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

  try {
    const res = await fetch(`/api/v1/units/${unitId}`);
    if (!res.ok) throw new Error("Unit not found");
    const unit = await res.json();
    STATE.currentUnit = unit;

    // Render Target Skills
    const skillsContainer = document.getElementById("unit-target-skills");
    if (skillsContainer && unit.target_skills) {
      skillsContainer.innerHTML = unit.target_skills.map(s => 
        `<span style="font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: var(--radius-sm); background: rgba(37, 99, 235, 0.1); color: var(--color-primary); font-family: var(--font-mono); font-weight: 600;">${s.skill_id} (${s.goal_level})</span>`
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

    // Render Timestamps
    const tsContainer = document.getElementById("video-timestamps");
    if (tsContainer) {
      if (unit.media && unit.media.length > 0 && unit.media[0].timestamps) {
        tsContainer.innerHTML = unit.media[0].timestamps.map(t => 
          `<div style="display: flex; justify-content: space-between; padding: 0.4rem 0.6rem; background: var(--bg-card-subtle); border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
            <span style="font-weight: 500;">${t.topic}</span>
            <span style="font-family: var(--font-mono); color: var(--color-primary); font-weight: 700;">${t.time}</span>
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
    feedback.innerHTML = `<span style="color: var(--color-danger); font-weight: 600;">Please provide an explanation.</span>`;
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
        ? `<span style="color: var(--color-success); font-weight: 700;">✓ Mental Model: Solid! Advancing to Step 2...</span>`
        : `<span style="color: var(--color-warning); font-weight: 700;">⚠ Mental Model: Shaky (${data.feedback}). Proceeding to practice...</span>`;
      
      await loadLedgerEntries();
      updateDashboardCounts();
      setTimeout(() => goToStep("predict"), 900);
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
  goToStep("practice");
}

// --- Interactive Execution in Playground ---
function executePlaygroundCode() {
  const code = document.getElementById("studio-editor").value;
  const terminal = document.getElementById("terminal-screen");
  const promptBox = document.getElementById("terminal-prompt-box");
  const stdinField = document.getElementById("stdin-field");
  const status = document.getElementById("execution-status");

  status.innerText = "Running...";

  if (code.includes("input(")) {
    terminal.innerHTML = `
      <div style="color: #64748b;">$ python solution.py</div>
      <div style="color: #facc15;">Executing: Paused on stdin...</div>
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

  try {
    const res = await fetch("/api/v1/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: code, timeout_seconds: 5.0 })
    });

    if (res.ok) {
      const result = await res.json();
      status.innerText = result.success ? "Exit Code 0" : "Execution Error";

      let outputHtml = `<div style="color: #64748b;">$ python solution.py</div>`;
      if (stdinInput) {
        outputHtml += `<div style="color: #94a3b8;">Enter citizen name: <strong style="color: #ffffff;">${escapeHtml(stdinInput)}</strong></div>`;
      }
      if (result.stdout) {
        outputHtml += `<div style="white-space: pre-wrap; color: #34d399;">${escapeHtml(result.stdout)}</div>`;
      }
      if (result.stderr) {
        outputHtml += `<div style="white-space: pre-wrap; color: #f87171;">${escapeHtml(result.stderr)}</div>`;
      }
      outputHtml += `<div style="color: #64748b; margin-block-start: 0.5rem;">[Process finished in ${result.duration_ms}ms with exit code ${result.exit_code}]</div>`;
      terminal.innerHTML = outputHtml;
    }
  } catch (err) {
    status.innerText = "Runner Error";
    terminal.innerHTML += `<div style="color: #f87171;">Failed to connect to execution runner: ${err.message}</div>`;
  }
}

async function verifyPlaygroundSolution() {
  const code = document.getElementById("studio-editor").value;
  const terminal = document.getElementById("terminal-screen");
  const status = document.getElementById("execution-status");

  if (!STATE.currentUnit || !STATE.currentUnit.test_code) {
    alert("No test suite available for this unit.");
    return;
  }

  status.innerText = "Verifying assertions...";

  try {
    const res = await fetch("/api/v1/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: code,
        test_code: STATE.currentUnit.test_code,
        timeout_seconds: 5.0
      })
    });

    if (res.ok) {
      const result = await res.json();
      if (result.success) {
        status.innerText = "Verified PASS";
        terminal.innerHTML = `
          <div style="color: #64748b;">$ uv run pytest test_solution.py</div>
          <div style="color: #34d399; font-weight: 700; font-size: 0.9rem;">✓ ALL ASSERTIONS PASSED (${result.duration_ms}ms)</div>
          <div style="color: #e2e8f0; margin-block-start: 0.5rem;">Evidence Ledger record appended: Strong (None).</div>
          <div style="color: #a7f3d0;">Progression updated: ${STATE.activeUnitId} Completed.</div>
        `;

        await fetch(`/api/v1/learners/default_learner/progress`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ unit_id: STATE.activeUnitId, status: "Completed" })
        });

        await loadLedgerEntries();
        updateDashboardCounts();
      } else {
        status.innerText = "Verification Failed";
        terminal.innerHTML = `
          <div style="color: #64748b;">$ uv run pytest test_solution.py</div>
          <div style="color: #f87171; font-weight: 700;">✗ VERIFICATION FAILED:</div>
          <div style="color: #fca5a5; white-space: pre-wrap;">${escapeHtml(result.stderr || result.stdout)}</div>
        `;
      }
    }
  } catch (err) {
    status.innerText = "Verify Error";
    terminal.innerHTML += `<div style="color: #f87171;">Verification request failed: ${err.message}</div>`;
  }
}

function clearTerminalScreen() {
  const terminal = document.getElementById("terminal-screen");
  if (terminal) terminal.innerHTML = `<div style="color: #64748b;">$ Terminal cleared. Click 'Run Code' or 'Verify Solution'.</div>`;
}

function updateLineNumbers() {
  const editor = document.getElementById("studio-editor");
  const lineNumbers = document.getElementById("studio-line-numbers");
  if (!editor || !lineNumbers) return;
  const count = editor.value.split("\n").length;
  lineNumbers.innerHTML = Array.from({length: Math.max(count, 12)}, (_, i) => i + 1).join("<br>");
}

function resetCurrentCode() {
  if (STATE.currentUnit && STATE.currentUnit.starter_code) {
    const editor = document.getElementById("studio-editor");
    if (editor) {
      editor.value = STATE.currentUnit.starter_code;
      updateLineNumbers();
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
    <div class="card" onclick="loadUnit('${u.unit_id}'); showView('unit-studio');" style="cursor: pointer; transition: transform 0.15s ease;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='none'">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-block-end: 0.35rem;">
        <span style="font-family: var(--font-mono); font-weight: 800; color: var(--color-primary);">${u.unit_id}</span>
        <span style="font-size: 0.75rem; background: rgba(34, 197, 94, 0.1); color: var(--color-success); padding: 0.1rem 0.4rem; border-radius: var(--radius-sm); font-weight: 600;">AVAILABLE</span>
      </div>
      <div style="font-weight: 700; font-size: 0.95rem; margin-block-end: 0.25rem;">${u.title}</div>
      <p style="font-size: 0.8rem; color: var(--text-muted); margin-block-end: 0.75rem;">${u.concept_line}</p>
      <div style="display: flex; gap: 0.35rem; flex-wrap: wrap;">
        ${u.target_skills.map(s => `<span style="font-size: 0.7rem; padding: 0.1rem 0.35rem; border-radius: 4px; background: var(--bg-card-subtle); color: var(--text-main); font-family: var(--font-mono);">${s.skill_id}</span>`).join("")}
      </div>
    </div>
  `).join("");

  container1.innerHTML = stage1Units.map(u => `
    <div class="card" style="opacity: 0.8;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-block-end: 0.35rem;">
        <span style="font-family: var(--font-mono); font-weight: 800; color: var(--text-muted);">${u.unit_id}</span>
        <span style="font-size: 0.75rem; background: var(--bg-card-subtle); color: var(--text-muted); padding: 0.1rem 0.4rem; border-radius: var(--radius-sm);">STAGE 1</span>
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
    STATE.recentSearches = raw ? JSON.parse(raw) : ["input()", "print()", "execution order", "variables"];
  } catch {
    STATE.recentSearches = ["input()", "print()", "execution order", "variables"];
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
    <button onclick="clearRecentSearches()" style="background: none; border: none; color: var(--text-muted); font-size: 0.7rem; cursor: pointer; text-decoration: underline; margin-inline-start: 0.25rem;">Clear</button>
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
      <div class="card" style="text-align: center; padding: 3rem 1.5rem; background: var(--bg-card-subtle); border-style: dashed;">
        <div style="font-size: 2.25rem; margin-block-end: 0.5rem;">📚</div>
        <h3 style="font-size: 1.1rem; font-weight: 700; margin-block-end: 0.35rem;">Concept Library Database (Resting Mode)</h3>
        <p style="color: var(--text-muted); font-size: 0.85rem; max-inline-size: 500px; margin-inline: auto;">
          Concepts are stored in the database as markdown notes and surface <strong>only when searched or clicked via wiki link</strong> in your lesson notes.
        </p>
        <div style="margin-block-start: 1rem; display: flex; justify-content: center; gap: 0.5rem;">
          <button onclick="applyRecentSearch('input()')" class="btn">Try "input()"</button>
          <button onclick="applyRecentSearch('execution order')" class="btn">Try "execution order"</button>
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
          Try searching for built-ins (<code>input</code>, <code>print</code>), syntax (<code>variables</code>, <code>f-strings</code>), or invariants (<code>sequential execution</code>).
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
        <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
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

    // Add to recent searches
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
    // Escape closes drawer
    if (e.key === "Escape") {
      closeConceptDrawer();
    }
  });
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
