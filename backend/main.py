import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.schemas.custom_types import AuditRequest, AuditResponse
from web_scraper.scraper import scrape_metrics
from ai.orchestrator import run_audit
from pathlib import Path


app = FastAPI(title="Website Audit Tool")

# ── CORS — allows the frontend (different port) to call the API ───────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # fine for a local demo/assessment
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files 
BASE_DIR = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "interface"), name="static")




# ROUTES
@app.get("/")
def serve_frontend():
    """Serves the frontend dashboard."""
    return FileResponse(BASE_DIR / "interface" / "index.html")


@app.post("/audit", response_model=AuditResponse)
def audit(request: AuditRequest):
    """
    1. Scrapes factual metrics from the URL
    2. Passes metrics to AI orchestrator
    3. Returns merged result to frontend
    """

    url = str(request.url)

    #Scrape the URL 
    try:
        metrics = scrape_metrics(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Run AI analysis
    try:
        ai_result = run_audit(metrics)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Merge and return 

    # Remove internal field before sending to frontend
    metrics.pop("_page_text", None)

    return {
        **metrics,
        "insights": ai_result["insights"],
        "recommendations": ai_result["recommendations"],
    }


@app.get("/logs")
def get_logs():
    """
    Returns prompt logs 
    """
    
    logs_path = Path(__file__).parent / "logs" / "prompt_logs.json"

    if not logs_path.exists():
        return {"logs": []}

    with open(logs_path, "r") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            return {"logs": []}

    return {"logs": logs}
