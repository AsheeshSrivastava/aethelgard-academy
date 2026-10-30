/**
 * Aethelgard Academy Web Platform Client
 * Production vanilla JS application controller.
 */

const STATE = {
  activeView: "dashboard",
  activeUnitId: "PY-0.1",
  activeStep: "explain",
  currentUnit: null,
  units: [],
  concepts: [],
  ledger: []
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", async () => {
  await loadUnitsCatalog();
  await loadConcepts();
  await loadLedgerEntries();
  await loadUnit(STATE.activeUnitId);
  updateDashboardCounts();
});

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
  if (viewName === "concept-library") renderConcepts(STATE.concepts);
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

    // Render Unit Metadata
    const skillsContainer = document.getElementById("unit-target-skills");
    if (skillsContainer && unit.target_skills) {
      skillsContainer.innerHTML = unit.target_skills.map(s => 
        `<span style="font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: var(--radius-sm); background: rgba(37, 99, 235, 0.1); color: var(--color-primary); font-family: var(--font-mono); font-weight: 600;">${s.skill_id} (${s.goal_level})</span>`
      ).join("");
    }

    // Render Lesson Markdown in Explain
    const explainBody = document.getElementById("explain-content");
    const explainUnitId = document.getElementById("explain-unit-id");
    if (explainUnitId) explainUnitId.innerText = unit.unit_id;
    if (explainBody) {
      explainBody.innerHTML = formatMarkdown(unit.lesson_markdown || unit.concept_line);
    }

    // Render Timestamps
    const tsContainer = document.getElementById("video-timestamps");
    if (tsContainer) {
      if (unit.media && unit.media.length > 0 && unit.media[0].timestamps) {
        tsContainer.innerHTML = unit.media[0].timestamps.map(t => 
          `<div style="display: flex; justify-content: space-between; padding: 0.35rem 0.5rem; background: var(--bg-card-subtle); border-radius: var(--radius-sm);">
            <span>${t.topic}</span>
            <span style="font-family: var(--font-mono); color: var(--color-primary); font-weight: 700;">${t.time}</span>
          </div>`
        ).join("");
      } else {
        tsContainer.innerHTML = `<div style="color: var(--text-muted);">No timestamp anchors available for this unit.</div>`;
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
  const promptBox = document.getElementById("terminal-interactive-prompt-box") || document.getElementById("terminal-prompt-box");
  const stdinField = document.getElementById("stdin-field");
  const status = document.getElementById("execution-status");

  status.innerText = "Running...";

  // Check if code uses interactive input()
  if (code.includes("input(")) {
    terminal.innerHTML = `
      <div style="color: #64748b;">$ python solution.py</div>
      <div style="color: #facc15;">Executing: Waiting for standard input (stdin)...</div>
    `;
    if (promptBox) promptBox.style.display = "flex";
    if (stdinField) {
      stdinField.value = "";
      stdinField.focus();
    }
    status.innerText = "Paused on stdin";
  } else {
    // Direct execution
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
        outputHtml += `<div style="color: #94a3b8;">Enter citizen name: <strong style="color: #ffffff;">${stdinInput}</strong></div>`;
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

        // Update progress in DB
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

// --- Line Numbers ---
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

// --- Concept Library KMS ---
async function loadConcepts() {
  try {
    const res = await fetch("/api/v1/concepts");
    if (res.ok) {
      STATE.concepts = await res.json();
      renderConcepts(STATE.concepts);
    }
  } catch (err) {
    console.error("Failed to load concepts:", err);
  }
}

function renderConcepts(conceptList) {
  const grid = document.getElementById("concept-cards-grid");
  if (!grid) return;

  grid.innerHTML = conceptList.map(c => `
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-block-end: 0.35rem;">
        <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--color-primary); font-weight: 700; letter-spacing: 0.05em;">${c.category}</span>
        <a href="${c.doc_url}" target="_blank" rel="noreferrer" style="font-size: 0.75rem; color: var(--text-accent); text-decoration: none;">python.org ↗</a>
      </div>
      <div style="font-weight: 800; font-size: 1rem; margin-block-end: 0.35rem;">${c.name}</div>
      <p style="font-size: 0.825rem; color: var(--text-main); margin-block-end: 0.5rem;">${c.summary}</p>
      <div style="background: var(--bg-card-subtle); padding: 0.5rem; border-radius: var(--radius-sm); font-size: 0.775rem; color: var(--text-muted); margin-block-end: 0.75rem;">
        <strong style="color: var(--text-main);">Execution Invariant:</strong> ${c.execution_rules}
      </div>
      <div style="display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap;">
        <span style="font-size: 0.75rem; color: var(--text-muted);">Units:</span>
        ${c.units.map(u => `<span onclick="loadUnit('${u}'); showView('unit-studio');" style="font-size: 0.7rem; font-family: var(--font-mono); padding: 0.1rem 0.35rem; border-radius: 4px; background: rgba(37, 99, 235, 0.1); color: var(--color-primary); cursor: pointer;">${u}</span>`).join("")}
      </div>
    </div>
  `).join("");
}

function filterConcepts(query) {
  const q = query.toLowerCase().trim();
  if (!q) {
    renderConcepts(STATE.concepts);
    return;
  }
  const filtered = STATE.concepts.filter(c => 
    c.name.toLowerCase().includes(q) || 
    c.summary.toLowerCase().includes(q) || 
    c.category.toLowerCase().includes(q) ||
    c.units.some(u => u.toLowerCase().includes(q))
  );
  renderConcepts(filtered);
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
  const conceptEl = document.getElementById("dash-concept-count");
  if (ledgerEl) ledgerEl.innerText = `${STATE.ledger.length} Verified Entries`;
  if (conceptEl) conceptEl.innerText = `${STATE.concepts.length} Concepts`;
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

function formatMarkdown(text) {
  if (!text) return "";
  // Lightweight markdown converter for headers, bold, code, and callouts
  return text
    .replace(/^### (.*$)/gim, '<h3 style="font-size: 0.95rem; font-weight: 700; margin-block-start: 1rem; margin-block-end: 0.35rem;">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 style="font-size: 1.1rem; font-weight: 800; margin-block-start: 1.25rem; margin-block-end: 0.5rem; color: var(--color-primary);">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 style="font-size: 1.25rem; font-weight: 800; margin-block-end: 0.5rem;">$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/`(.*?)`/gim, '<code style="font-family: var(--font-mono); background: var(--bg-card-subtle); padding: 0.15rem 0.35rem; border-radius: 4px; font-size: 0.8rem; color: var(--text-accent);">$1</code>')
    .replace(/\n\n/gim, '<p style="margin-block-end: 0.75rem; color: var(--text-muted);"></p>');
}
