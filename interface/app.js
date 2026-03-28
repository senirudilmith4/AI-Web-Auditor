// interface/app.js
const API_BASE = window.location.origin;


// DOM refs
const urlInput  = document.getElementById("urlInput");
const auditBtn  = document.getElementById("auditBtn");
const errorMsg  = document.getElementById("errorMsg");
const loader    = document.getElementById("loader");
const loaderText = document.getElementById("loaderText");
const results   = document.getElementById("results");

// Loader messages to cycle through while waiting 
const LOADER_STEPS = [
  "Fetching page...",
  "Extracting metrics...",
  "Analysing with Gemini...",
  "Structuring insights...",
];

let loaderInterval = null;

function startLoader() {
  loader.classList.remove("hidden");
  results.classList.add("hidden");
  hideError();

  let step = 0;
  loaderText.textContent = LOADER_STEPS[0];
  loaderInterval = setInterval(() => {
    step = (step + 1) % LOADER_STEPS.length;
    loaderText.textContent = LOADER_STEPS[step];
  }, 2000);
}

function stopLoader() {
  clearInterval(loaderInterval);
  loader.classList.add("hidden");
}

// Error helpers 
function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove("hidden");
}

function hideError() {
  errorMsg.classList.add("hidden");
  errorMsg.textContent = "";
}

//  Safely set text content (fallback to "—") 
function setText(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = (value !== null && value !== undefined && value !== "")
    ? value
    : "—";
}

// Render metrics panel 
function renderMetrics(data) {
  document.getElementById("auditedUrl").textContent = data.url;

  // Meta
  setText("metaTitle", data.meta.title);
  setText("metaDesc",  data.meta.description);

  // Content
  setText("wordCount", data.content.word_count.toLocaleString());

  // CTAs
  setText("ctaCount", data.ctas.total);

  // Images
  setText("imageCount", data.images.total);
  setText("missingAlt", data.images.missing_alt);
  document.getElementById("missingAltPct").textContent =
    data.images.total > 0
      ? `${data.images.pct_missing_alt}% of images`
      : "";

  // Headings
  setText("h1Count", data.headings.h1_count);
  setText("h2Count", data.headings.h2_count);
  setText("h3Count", data.headings.h3_count);

  // Links
  setText("internalLinks", data.links.internal_count);
  setText("externalLinks", data.links.external_count);
}

// Render AI insights 
function renderInsights(insights) {
  setText("insightSeo",     insights.seo_structure);
  setText("insightMsg",     insights.messaging_clarity);
  setText("insightCta",     insights.cta_usage);
  setText("insightContent", insights.content_depth);
  setText("insightUx",      insights.ux_structure);
}

// Render recommendations
function renderRecommendations(recs) {
  const list = document.getElementById("recsList");
  list.innerHTML = "";

  recs
    .sort((a, b) => a.priority - b.priority)
    .forEach((rec, i) => {
      const card = document.createElement("div");
      card.className = "rec-card";
      card.style.animationDelay = `${i * 0.08}s`;
      card.innerHTML = `
        <div class="rec-priority">0${rec.priority}</div>
        <div>
          <div class="rec-title">${escapeHtml(rec.title)}</div>
          <p class="rec-reasoning">${escapeHtml(rec.reasoning)}</p>
        </div>
      `;
      list.appendChild(card);
    });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Main audit function 
async function runAudit() {
  const url = urlInput.value.trim();

  // Basic client-side validation
  if (!url) {
    showError("Please enter a URL.");
    return;
  }
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    showError("URL must start with http:// or https://");
    return;
  }

  auditBtn.disabled = true;
  startLoader();

  try {
    const response = await fetch(`${API_BASE}/audit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await response.json();

    if (!response.ok) {
      // FastAPI returns { detail: "..." } on errors
      throw new Error(data.detail || `Server error: ${response.status}`);
    }

    // Render everything
    renderMetrics(data);
    renderInsights(data.insights);
    renderRecommendations(data.recommendations);

    // Show results
    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (err) {
    showError(err.message || "Something went wrong. Check the console.");
    console.error("Audit error:", err);
  } finally {
    stopLoader();
    auditBtn.disabled = false;
  }
}

// Event listeners 
auditBtn.addEventListener("click", runAudit);

// Allow Enter key to trigger audit
urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runAudit();
});
