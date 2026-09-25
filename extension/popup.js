function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

// Municipal Tender Watchdog - Popup Logic
const API_BASE = "http://127.0.0.1:8000";

let currentExtractedData = null;
let currentAnalysis = null;
let currentTabId = null;
let currentSourceUrl = null;

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Check backend health
  checkBackendHealth();

  // 2. Query active tab and detect page content
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs || !tabs[0]) return;
    currentTabId = tabs[0].id;
    currentSourceUrl = tabs[0].url;

    chrome.tabs.sendMessage(currentTabId, { action: "detectPage" }, (response) => {
      if (chrome.runtime.lastError || !response) {
        showView("notDetectedView");
        return;
      }

      if (response.isTender) {
        showDetectedView(response);
      } else {
        showView("notDetectedView");
      }
    });
  });

  // Event Listeners
  document.getElementById("openDemoBtn").addEventListener("click", () => {
    chrome.tabs.create({ url: chrome.runtime.getURL("../demo/tender.html") });
  });

  document.getElementById("analyzeBtn").addEventListener("click", () => {
    startAnalysis();
  });

  document.getElementById("reanalyzeBtn").addEventListener("click", () => {
    startAnalysis();
  });

  document.getElementById("viewEvidenceBtn").addEventListener("click", () => {
    togglePanel("evidencePanel");
  });

  document.getElementById("closeEvidenceBtn").addEventListener("click", () => {
    hidePanel("evidencePanel");
  });

  document.getElementById("generateRtiBtn").addEventListener("click", () => {
    loadRtiDraft();
    showPanel("rtiPanel");
  });

  document.getElementById("closeRtiBtn").addEventListener("click", () => {
    hidePanel("rtiPanel");
  });

  document.getElementById("copyRtiBtn").addEventListener("click", () => {
    copyRtiText();
  });
});

async function checkBackendHealth() {
  const pill = document.getElementById("backendStatus");
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      pill.textContent = "API Connected";
      pill.className = "backend-pill online";
    } else {
      throw new Error("HTTP error");
    }
  } catch (e) {
    pill.textContent = "API Offline";
    pill.className = "backend-pill offline";
  }
}

function showView(viewId) {
  const views = ["notDetectedView", "detectedView", "loadingView", "resultView"];
  views.forEach((v) => {
    const el = document.getElementById(v);
    if (el) {
      if (v === viewId) el.classList.remove("hidden");
      else el.classList.add("hidden");
    }
  });
}

function showDetectedView(data) {
  currentExtractedData = data;
  const s = data.structured || {};
  const isLive = Boolean(data.isLivePortal || (currentSourceUrl && currentSourceUrl.includes("tntenders.gov.in")));

  const badgeText = document.getElementById("detectedBadgeText");
  const portalTag = document.getElementById("detPortal");
  const analyzeBtn = document.getElementById("analyzeBtn");

  if (badgeText) {
    badgeText.textContent = isLive ? "LIVE TENDER DETECTED" : "TENDER DETECTED (DEMO)";
  }
  if (portalTag) {
    portalTag.textContent = isLive ? "tntenders.gov.in (Official)" : (data.portalHost || "Local Demo Environment");
  }
  if (analyzeBtn) {
    analyzeBtn.textContent = isLive ? "ANALYZE LIVE TENDER" : "ANALYZE TENDER";
  }

  document.getElementById("detTenderId").textContent = s.tender_id || "Available upon scan";
  document.getElementById("detAuthority").textContent = s.authority || "Coimbatore Municipal Authority";
  document.getElementById("detLocation").textContent = s.location || "Coimbatore Urban";
  showView("detectedView");
}

async function startAnalysis() {
  showView("loadingView");
  setStep("step1", "active");

  try {
    // Stage 1: Send raw page text + hints to /extract
    const extractRes = await fetch(`${API_BASE}/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_page_text: currentExtractedData ? currentExtractedData.raw_page_text : "",
        structured_hints: currentExtractedData ? currentExtractedData.structured : {},
        source_url: currentSourceUrl
      })
    });

    if (!extractRes.ok) throw new Error("Extraction failed");
    const extractedTender = await extractRes.json();

    setStep("step1", "done");
    setStep("step2", "active");

    // Small UI delay for smooth progression
    await new Promise((r) => setTimeout(r, 400));
    setStep("step2", "done");
    setStep("step3", "active");

    // Stage 2 & 3: Run /analyze
    const analyzeRes = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tender: extractedTender })
    });

    if (!analyzeRes.ok) throw new Error("Analysis failed");
    const analysis = await analyzeRes.json();
    currentAnalysis = analysis;

    setStep("step3", "done");
    await new Promise((r) => setTimeout(r, 300));

    displayAnalysisResults(analysis);
  } catch (err) {
    console.error(err);
    alert("Analysis encountered an error: " + err.message + "\nPlease verify the backend is running at http://127.0.0.1:8000");
    showView("detectedView");
  }
}

function setStep(stepId, state) {
  const el = document.getElementById(stepId);
  if (!el) return;
  el.className = "step " + state;
}

function displayAnalysisResults(analysis) {
  showView("resultView");
  hidePanel("evidencePanel");
  hidePanel("rtiPanel");

  const badge = document.getElementById("signalBadge");
  const icon = document.getElementById("signalIcon");
  const headline = document.getElementById("signalHeadline");
  const explanation = document.getElementById("explanationText");
  const notice = document.getElementById("portalSearchNotice");

  explanation.textContent = analysis.explanation;

  // Show portal search CAPTCHA interaction notice if returned
  if (notice) {
    if (analysis.portal_search_note) {
      notice.textContent = `ℹ️ ${analysis.portal_search_note} Historical evaluation conducted against verified SQLite cache.`;
      notice.classList.remove("hidden");
    } else {
      notice.classList.add("hidden");
    }
  }

  if (!analysis.is_urban_scope || analysis.status_code === "INFO") {
    badge.className = "signal-badge signal-info";
    icon.textContent = "⚪";
    headline.textContent = analysis.status_headline || "Outside Urban Scope";
  } else if (analysis.status_code === "RED" || analysis.repetition_flag) {
    badge.className = "signal-badge signal-red";
    icon.textContent = "🔴";
    headline.textContent = analysis.status_headline || "Repeated procurement detected";
  } else if (analysis.status_code === "ORANGE" || analysis.silence_flag) {
    badge.className = "signal-badge signal-orange";
    icon.textContent = "🟠";
    headline.textContent = analysis.status_headline || "Completion evidence gap";
  } else if (analysis.status_code === "ORANGE_RED") {
    badge.className = "signal-badge signal-red";
    icon.textContent = "🔴";
    headline.textContent = analysis.status_headline || "Repeated procurement & Completion gap";
  } else {
    badge.className = "signal-badge signal-green";
    icon.textContent = "🟢";
    headline.textContent = analysis.status_headline || "No accountability signal detected";
  }

  // Populate Evidence Section & Fields
  const curr = analysis.current_tender || {};
  const hist = analysis.similar_tender;
  const evidenceList = analysis.evidence_list || [];

  // Update Drawer Elements
  document.getElementById("evCurrId").textContent = curr.tender_id || "—";
  document.getElementById("evCurrAuth").textContent = curr.authority || "—";
  document.getElementById("evCurrLoc").textContent = curr.locality || "—";
  document.getElementById("evCurrWardZone").textContent = [curr.zone, curr.ward].filter(Boolean).join(" / ") || "—";
  document.getElementById("evCurrTitle").textContent = curr.title || "—";
  document.getElementById("evCurrDate").textContent = curr.published_date || "—";
  document.getElementById("evCurrVal").textContent = curr.tender_value ? `₹ ${curr.tender_value.toLocaleString("en-IN")}` : "Not Disclosed";

  // Current tender source URL link
  const currSourceUrl = curr.source_url || (evidenceList.find(e => e.tender_id === curr.tender_id) || {}).source_url;
  const currSourceLink = document.getElementById("evCurrSourceLink");
  if (currSourceLink) {
    if (currSourceUrl) {
      currSourceLink.href = currSourceUrl;
      currSourceLink.classList.remove("hidden");
    } else {
      currSourceLink.classList.add("hidden");
    }
  }

  const histTable = document.getElementById("histMatchTable");
  const noHistNote = document.getElementById("noHistMatchNote");
  const histSourceLink = document.getElementById("evHistSourceLink");

  if (hist) {
    histTable.classList.remove("hidden");
    noHistNote.classList.add("hidden");
    document.getElementById("evHistId").textContent = hist.tender_id || "—";
    document.getElementById("evHistAuth").textContent = hist.authority || "—";
    document.getElementById("evHistLoc").textContent = hist.locality || "—";
    document.getElementById("evHistWardZone").textContent = [hist.zone, hist.ward].filter(Boolean).join(" / ") || "—";
    document.getElementById("evHistTitle").textContent = hist.title || "—";
    document.getElementById("evHistDate").textContent = hist.published_date || "—";
    document.getElementById("evHistScore").textContent = `${analysis.similarity_score} (${Math.round(analysis.similarity_score * 100)}%)`;
    document.getElementById("evHistTime").textContent = analysis.time_difference_days != null ? `${analysis.time_difference_days} days prior` : "Recent";

    const histSourceUrl = hist.source_url || (evidenceList.find(e => e.tender_id === hist.tender_id) || {}).source_url;
    if (histSourceLink) {
      if (histSourceUrl) {
        histSourceLink.href = histSourceUrl;
        histSourceLink.classList.remove("hidden");
      } else {
        histSourceLink.classList.add("hidden");
      }
    }
  } else {
    histTable.classList.add("hidden");
    noHistNote.classList.remove("hidden");
    if (histSourceLink) histSourceLink.classList.add("hidden");
  }

  // Official source URL fallback
  const sourceLink = document.getElementById("evSourceLink");
  if (sourceLink) {
    const mainSource = currSourceUrl || (hist ? hist.source_url : null);
    if (mainSource) {
      sourceLink.href = mainSource;
      sourceLink.classList.remove("hidden");
    } else {
      sourceLink.classList.add("hidden");
    }
  }

  // Populate Visible Evidence Cards Section
  const cardsContainer = document.getElementById("evidenceCardsContainer");
  const countBadge = document.getElementById("evidenceCountBadge");
  if (cardsContainer) {
    cardsContainer.innerHTML = "";

    // Use evidence_list if populated, otherwise synthesize from curr & hist
    let displayItems = evidenceList.slice();
    if (displayItems.length === 0) {
      displayItems.push({
        tender_id: curr.tender_id || "CURRENT",
        title: curr.title || "Current Tender Under Review",
        authority: curr.authority || "Municipal Authority",
        locality: curr.locality || "Coimbatore",
        published_date: curr.published_date,
        similarity_score: 1.0,
        time_difference_days: 0,
        source_url: currSourceUrl,
        evidence_type: "CURRENT_TENDER"
      });
      if (hist) {
        displayItems.push({
          tender_id: hist.tender_id,
          title: hist.title,
          authority: hist.authority,
          locality: hist.locality || "Coimbatore",
          published_date: hist.published_date,
          similarity_score: analysis.similarity_score,
          time_difference_days: analysis.time_difference_days,
          source_url: hist.source_url,
          evidence_type: "HISTORICAL_MATCH"
        });
      }
    }

    if (countBadge) {
      countBadge.textContent = `${displayItems.length} Record${displayItems.length === 1 ? '' : 's'}`;
    }

    displayItems.forEach((ev) => {
      const isCurrent = ev.evidence_type === "CURRENT_TENDER" || ev.tender_id === curr.tender_id;
      const card = document.createElement("div");
      card.className = `evidence-card ${isCurrent ? 'card-current' : 'card-historical'}`;

      const scoreText = ev.similarity_score != null
        ? (isCurrent ? "Baseline (1.0)" : `${Math.round(ev.similarity_score * 100)}% Match`)
        : "";

      const timeText = ev.time_difference_days != null
        ? (ev.time_difference_days === 0 ? "Current Record" : `${ev.time_difference_days} days prior`)
        : "—";

      card.innerHTML = `
        <div class="evidence-card-top">
          <span class="evidence-tag ${isCurrent ? 'tag-current' : 'tag-historical'}">
            ${isCurrent ? 'Current Tender' : 'Historical Match'}
          </span>
          ${scoreText ? `<span class="evidence-score-pill">${scoreText}</span>` : ''}
        </div>
        <div class="evidence-card-title">${escapeHtml(ev.title || ev.tender_id)}</div>
        <div class="evidence-grid">
          <div><span class="lbl">Tender ID:</span> <strong>${escapeHtml(ev.tender_id || '—')}</strong></div>
          <div><span class="lbl">Authority:</span> ${escapeHtml(ev.authority || '—')}</div>
          <div><span class="lbl">Locality:</span> ${escapeHtml(ev.locality || '—')}</div>
          <div><span class="lbl">Published:</span> ${escapeHtml(ev.published_date || '—')}</div>
          <div class="grid-full"><span class="lbl">Time Horizon:</span> ${escapeHtml(timeText)}</div>
        </div>
        ${ev.source_url ? `
        <div class="evidence-source-action">
          <a href="${escapeHtml(ev.source_url)}" target="_blank" rel="noopener noreferrer" class="source-link">
            Open Official Source ↗
          </a>
        </div>` : ''}
      `;
      cardsContainer.appendChild(card);
    });
  }
}

async function loadRtiDraft() {
  if (!currentAnalysis) return;
  const curr = currentAnalysis.current_tender || {};
  const draftBox = document.getElementById("rtiDraftContent");
  draftBox.textContent = "Generating custom RTI application draft...";

  try {
    const res = await fetch(`${API_BASE}/rti-draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tender_id: curr.tender_id || "TENDER_ID",
        authority: curr.authority,
        title: curr.title,
        reference_no: curr.reference_no,
        silence_flag: currentAnalysis.silence_flag,
        repetition_flag: currentAnalysis.repetition_flag,
        similar_tender_id: currentAnalysis.similar_tender ? currentAnalysis.similar_tender.tender_id : null,
        similarity_score: currentAnalysis.similarity_score
      })
    });

    if (res.ok) {
      const data = await res.json();
      draftBox.textContent = data.full_draft_text;
    } else {
      draftBox.textContent = "Failed to load RTI draft from backend.";
    }
  } catch (e) {
    draftBox.textContent = "Error generating RTI draft: " + e.message;
  }
}

function copyRtiText() {
  const text = document.getElementById("rtiDraftContent").textContent;
  navigator.clipboard.writeText(text).then(() => {
    const fb = document.getElementById("copyFeedback");
    fb.classList.remove("hidden");
    setTimeout(() => fb.classList.add("hidden"), 2500);
  });
}

function togglePanel(panelId) {
  const panel = document.getElementById(panelId);
  if (panel.classList.contains("hidden")) {
    showPanel(panelId);
  } else {
    hidePanel(panelId);
  }
}

function showPanel(panelId) {
  document.getElementById("evidencePanel").classList.add("hidden");
  document.getElementById("rtiPanel").classList.add("hidden");
  document.getElementById(panelId).classList.remove("hidden");
}

function hidePanel(panelId) {
  document.getElementById(panelId).classList.add("hidden");
}
