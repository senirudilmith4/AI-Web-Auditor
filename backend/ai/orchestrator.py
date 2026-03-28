import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)
model="gemini-2.5-flash"



LOGS_PATH = Path(__file__).parent.parent / "logs" / "prompt_logs.json"
LOGS_PATH.parent.mkdir(exist_ok=True)



# 1. SYSTEM PROMPT

SYSTEM_PROMPT = """
You are an expert SEO and conversion rate optimization (CRO) analyst working for a 
digital marketing agency that builds high-performing marketing websites.

Your job is to audit a webpage using structured metrics that have been extracted 
from it, along with a sample of its visible text content.

You must analyze the page across these five dimensions:
1. SEO Structure      — headings, meta tags, content depth signals
2. Messaging Clarity  — how clearly the page communicates its value proposition
3. CTA Usage          — whether calls-to-action are sufficient, well-placed, and compelling
4. Content Depth      — whether the content is substantial enough to rank and convert
5. UX / Structure     — obvious structural or navigational concerns based on the data

STRICT RULES:
- Every insight MUST reference a specific metric from the provided data (e.g. "With only 1 H1...")
- Do NOT give generic advice like "add more content" without tying it to the metrics
- Do NOT make up metrics or assume data not provided
- Be direct, specific, and concise — like a senior analyst, not a chatbot
- You MUST respond with valid JSON only. No markdown, no explanation outside the JSON.

Your response must follow this exact JSON schema:
{
  "insights": {
    "seo_structure": "string",
    "messaging_clarity": "string",
    "cta_usage": "string",
    "content_depth": "string",
    "ux_structure": "string"
  },
  "recommendations": [
    {
      "priority": 1,
      "title": "string",
      "reasoning": "string"
    }
  ]
}

Provide exactly 4 recommendations, ordered by priority (1 = most critical).
""".strip()


# 2. USER PROMPT BUILDER
def build_user_prompt(metrics: dict) -> str:
    """
    Constructs the user prompt by injecting structured metrics into a template.
    The AI receives clean JSON data — not raw HTML or unstructured text.
    """

    # Extract the page text sample for AI context (capped at 3000 words to avoid token limits)
    page_text = metrics.get("_page_text", "")

    # Re-structure the metrics into a clean JSON format for the AI, ensuring all relevant data is included
    structured_metrics = {
        "url": metrics["url"],
        "meta_title": metrics["meta"]["title"],
        "meta_description": metrics["meta"]["description"],
        "headings": {
            "h1_count": metrics["headings"]["h1_count"],
            "h1_texts": metrics["headings"]["h1"],
            "h2_count": metrics["headings"]["h2_count"],
            "h3_count": metrics["headings"]["h3_count"],
        },
        "word_count": metrics["content"]["word_count"],
        "images": {
            "total": metrics["images"]["total"],
            "missing_alt_count": metrics["images"]["missing_alt"],
            "pct_missing_alt": metrics["images"]["pct_missing_alt"],
        },
        "links": {
            "internal": metrics["links"]["internal_count"],
            "external": metrics["links"]["external_count"],
        },
        "cta_count": metrics["ctas"]["total"],
    }

    user_prompt = f"""
Please audit the following webpage.

## Extracted Metrics (factual, do not alter): 
{json.dumps(structured_metrics, indent=2)}

## Page Content Sample (first ~3000 words of visible text):
{page_text}

Using the metrics and content above, generate your structured audit response 
as valid JSON matching the schema provided in your instructions.
""".strip()

    return user_prompt, structured_metrics  


# 3. PROMPT LOGGING
def save_prompt_log(url: str, user_prompt: str, raw_response: str, structured_metrics: dict):
 
    """
    Saves the full prompt trace to logs/prompt_logs.json.

    """

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "url": url,
        "system_prompt": SYSTEM_PROMPT,
        "structured_inputs": structured_metrics,
        "user_prompt": user_prompt,
        "raw_model_output": raw_response,
    }

    # Load existing logs if file exists
    if LOGS_PATH.exists():
        with open(LOGS_PATH, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append(log_entry)

    with open(LOGS_PATH, "w") as f:
        json.dump(logs, f, indent=2)



# 4. MAIN ORCHESTRATOR FUNCTION
def run_audit(metrics: dict) -> dict:

    """
    Takes raw scraper output, runs AI analysis, returns structured result.

    """

    # Build user prompt with structured metrics
    user_prompt, structured_metrics = build_user_prompt(metrics)

    # Call Gemini
    try:
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=4000,
            )
        )
                
        raw_response = response.text

    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")

    # Log the prompt and response for transparency and debugging
    save_prompt_log(metrics["url"], user_prompt, raw_response, structured_metrics)

    
    ai_result = parse_ai_response(raw_response)

    return ai_result


# 5. RESPONSE PARSER
def parse_ai_response(raw: str) -> dict:
    """
    Parses Gemini's raw text output into a clean Python dict.
    Handles the case where the model wraps JSON in markdown code fences.
    """

    # Strip whitespace and remove markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Remove the opening fence line (e.g. ```json)
        cleaned = cleaned.split("\n", 1)[1]
        # Remove the closing fence if present
        if cleaned.strip().endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI response was not valid JSON: {e}\nRaw output:\n{raw}")

    # Validate expected keys exist
    if "insights" not in parsed or "recommendations" not in parsed:
        raise ValueError(f"AI response missing required keys. Got: {list(parsed.keys())}")

    return parsed