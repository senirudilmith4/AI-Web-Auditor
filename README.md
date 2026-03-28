# SiteScopeAI — AI-Powered Website Audit Tool

A lightweight internal tool that accepts a single URL, extracts factual page metrics, and uses Gemini 2.5 Flash to generate structured SEO, CRO, and UX insights grounded in those metrics.


---

## Live Demo

🔗 **[SiteScopeAI.onrender.com](https://ai-web-auditor.onrender.com)**

> Note: Render free-tier instances spin down after inactivity. The first request may take 30–60 seconds to wake up.

---

## Project Structure

```
WebAuditor/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app — routes, request/response models
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── scrape.py        # Metric extraction via requests + BeautifulSoup
│   ├── ai/
│   │   ├── __init__.py
│   │   └── orchestrator.py  # Prompt construction, Gemini API call, logging
│   └── logs/
│       └── prompt_logs.json # Auto-written after every audit run
├── interface/
│   ├── index.html           # Single-page dashboard
│   ├── style.css            # Styling
│   └── app.js               # Fetch, render, error handling
├── .env                     # GEMINI_API_KEY (not committed)
├── requirements.txt
├── run.py
└── README.md
```

---

## Setup Instructions (Local)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd WebAuditor
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

Get a free key at [aistudio.google.com](https://aistudio.google.com).

### 5. Run the server

```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Open the dashboard

Visit `http://localhost:8000` in your browser.

---

## Deployment (Render)

The app is deployed on [Render](https://render.com) as a single web service.

**Render configuration:**

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Build command | `pip install -r ../requirements.txt` |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Environment variable | `GEMINI_API_KEY` → set in Render dashboard |

The `GEMINI_API_KEY` is set as an environment variable in the Render dashboard — never committed to the repository.

---

## How It Works

```
User enters URL
      ↓
POST /audit  (FastAPI)
      ↓
scrape.py  →  fetches page, extracts raw metrics
      ↓
orchestrator.py  →  builds structured prompt, calls Gemini 2.5 Flash
      ↓
logs/prompt_logs.json  ←  full trace written here
      ↓
FastAPI returns merged JSON to frontend
      ↓
Dashboard renders metrics, insights, and recommendations
```

The scraping layer and the AI layer are fully decoupled. The AI receives only clean, structured JSON — never raw HTML.

---

## Metrics Extracted

All metrics are extracted directly from the page with no AI involvement:

| Metric | Method |
|---|---|
| Word count | Visible text after stripping `<script>` and `<style>` tags |
| H1 / H2 / H3 counts | BeautifulSoup tag search |
| Meta title & description | `<title>` and `<meta name="description">` |
| Total images & missing alt text | `<img>` tags, checking `alt` attribute |
| Internal vs external links | `<a href>` tags parsed against base domain |
| CTA count | `<button>` tags + `<a>` tags matching action keywords |

---

## AI Design Decisions

### 1. Structured inputs, not raw HTML

The AI never sees raw HTML. Before calling Gemini, the scraper output is reshaped into a clean JSON object containing only the relevant metrics. This keeps the prompt focused, reduces token usage, and makes the AI's reasoning verifiable against real data.

### 2. System prompt engineering

The system prompt establishes a clear role ("SEO and CRO analyst at a digital marketing agency") and enforces strict grounding rules:

- Every insight **must** reference a specific metric (e.g. "With only 1 H1...")
- No generic advice without data justification
- Response must be **valid JSON only** — no markdown, no preamble

This prevents the model from producing generic filler and forces it to behave like an analyst, not a chatbot.

### 3. Structured JSON output schema

Gemini is given an exact JSON schema to follow:

```json
{
  "insights": {
    "seo_structure": "string",
    "messaging_clarity": "string",
    "cta_usage": "string",
    "content_depth": "string",
    "ux_structure": "string"
  },
  "recommendations": [
    { "priority": 1, "title": "string", "reasoning": "string" }
  ]
}
```

Structured output makes the response directly renderable by the frontend without additional parsing logic beyond JSON deserialization.

### 4. Temperature set to 0.4

Lower temperature produces more factual, consistent outputs — appropriate for an audit tool where accuracy matters more than creativity. A higher temperature would risk the model embellishing or inventing metric references.

### 5. Prompt logs saved before parsing

The raw model output is written to `logs/prompt_logs.json` **before** any parsing occurs. This means even if parsing fails, the full trace is preserved for debugging. Each log entry contains:

- Timestamp and URL
- The system prompt used
- The structured JSON inputs sent to the model
- The full user prompt as constructed
- The raw model output before any formatting

---

## Prompt Logs

Every audit run appends a full trace to `backend/logs/prompt_logs.json`.

You can also view logs directly at:

```
https://pageaudit.onrender.com/logs
```

Or locally at `http://localhost:8000/logs`.

Example log entry structure:

```json
{
  "timestamp": "2025-01-15T10:32:00Z",
  "url": "https://example.com",
  "system_prompt": "You are an expert SEO and CRO analyst...",
  "structured_inputs": {
    "meta_title": "Example — Home",
    "word_count": 1315,
    "cta_count": 9,
    "headings": { "h1_count": 1, "h2_count": 5, "h3_count": 3 }
  },
  "user_prompt": "Please audit the following webpage...",
  "raw_model_output": "{ \"insights\": { ... } }"
}
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the frontend dashboard |
| `POST` | `/audit` | Runs a full audit on a given URL |
| `GET` | `/logs` | Returns all prompt logs as JSON |
| `GET` | `/docs` | Auto-generated FastAPI interactive docs |

### POST /audit

**Request:**
```json
{ "url": "https://example.com" }
```

**Response:**
```json
{
  "url": "https://example.com",
  "meta": { "title": "...", "description": "..." },
  "headings": { "h1_count": 1, "h2_count": 5, "h3_count": 3 },
  "content": { "word_count": 1315 },
  "images": { "total": 89, "missing_alt": 0, "pct_missing_alt": 0 },
  "links": { "internal_count": 33, "external_count": 4 },
  "ctas": { "total": 9 },
  "insights": { "seo_structure": "...", "messaging_clarity": "...", ... },
  "recommendations": [ { "priority": 1, "title": "...", "reasoning": "..." } ]
}
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Scraping | Requests, BeautifulSoup4 |
| AI | Gemini 2.5 Flash (google-genai SDK) |
| Frontend | Plain HTML, CSS, Vanilla JS |
| Deployment | Render |
| Config | python-dotenv |

---

## Trade-offs

**BeautifulSoup over headless browser** — BS4 is fast and sufficient for static or server-rendered pages. It will miss content rendered entirely by JavaScript (e.g. React SPAs). A headless browser like Playwright would handle JS-rendered pages but adds significant complexity and latency for a 24-hour scope.

**Single-page only** — The tool audits one URL at a time. Multi-page crawling would require a link queue, rate limiting, and result aggregation — meaningful scope increase not warranted here.

**Gemini JSON output via prompt instruction** — Rather than using a formal structured output API, JSON structure is enforced through the system prompt and a response parser with fence-stripping. This is simpler and works reliably for this schema size, though a formal function-calling or structured output API would be more robust at scale.

**CTA detection by keyword matching** — CTAs are identified by matching button text and link text against a list of known action phrases. This works well for standard marketing pages but will miss custom or non-English CTAs. A more robust approach would use semantic similarity.

---

## What I Would Improve With More Time

**Multi-page crawling** — Follow internal links up to a configurable depth and aggregate metrics across the full site. This would shift the tool from a single-page snapshot to a genuine site-wide audit, surfacing patterns like inconsistent heading structure across pages or CTAs that only appear on certain entry points.

**Scoring and grading system per category** — Assign a numerical score (0–100) to each audit dimension (SEO, CRO, UX, etc.) based on the extracted metrics. Give the page an overall grade. This makes it trivial to compare pages against each other, track improvement after changes, and communicate results to non-technical stakeholders.

**PDF export of the report** — Generate a branded, downloadable PDF from the audit results. Agencies frequently need to share audit findings with clients who don't have tool access. A one-click export removes friction from that handoff entirely.

---

## Requirements

```
fastapi
uvicorn
requests
beautifulsoup4
google-genai
python-dotenv
```
