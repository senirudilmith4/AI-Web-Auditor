import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

try:
    # API test to verify key and model access
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hi"
    )
    print("✅ API key works! Model responded:", response.text)
except Exception as e:
    print("❌ API key or model issue:", e)

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