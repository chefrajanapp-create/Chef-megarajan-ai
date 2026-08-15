import os
import base64
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI

APP_NAME = "Chef Megarajan AI"
VERSION = "2.0.0"

app = FastAPI(title=APP_NAME, version=VERSION)

# GitHub Pages frontend + Render backend.
# API key is NEVER sent to the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chefrajanapp-create.github.io",
        "https://chef-megarajan-ai.onrender.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global client
    if client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise HTTPException(
                status_code=503,
                detail="OPENAI_API_KEY is not configured on the server."
            )
        client = OpenAI(api_key=key)
    return client


class CreateRecipeRequest(BaseModel):
    ingredients: List[str] = Field(min_length=1, max_length=40)
    servings: int = Field(default=4, ge=1, le=500)
    language: str = Field(default="ta")


class PantryScanRequest(BaseModel):
    image_base64: str
    mime_type: str = "image/jpeg"


def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()

    # Remove common markdown fences.
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(text[start:end + 1])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    raise ValueError("Model did not return valid JSON.")


@app.get("/")
def root():
    return {
        "service": "chef-megarajan-ai",
        "version": VERSION,
        "status": "live",
        "message": "Chef Megarajan AI backend is running."
    }


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "chef-megarajan-ai",
        "version": VERSION
    }


@app.get("/api/status")
def status():
    return {
        "recipes": "frontend dataset ready",
        "nutrition": "frontend dataset ready",
        "shopping": "ready",
        "pantry": "ready",
        "ai": "server-side OpenAI connection ready" if os.getenv("OPENAI_API_KEY") else "OPENAI_API_KEY missing",
        "market": "verified source not configured; no fake prices"
    }


@app.post("/api/ai/create-recipe")
def create_recipe(req: CreateRecipeRequest):
    ai = get_client()

    language = "Tamil" if req.language.lower().startswith("ta") else "English"
    ingredients = [x.strip() for x in req.ingredients if x.strip()]

    prompt = f"""
You are Chef Megarajan AI, a practical Indian/Tamil cooking assistant.

Create ONE realistic recipe using these available ingredients:
{json.dumps(ingredients, ensure_ascii=False)}

Servings: {req.servings}
Preferred language: {language}

Rules:
- Do not invent unavailable ingredients as if they were available.
- Optional ingredients may be suggested separately.
- Give practical quantities for the requested serving count.
- Keep the recipe suitable for a home or professional kitchen.
- If an ingredient is ambiguous, make a reasonable cooking assumption.
- Never give medical claims.
- Return ONLY valid JSON. No markdown.

JSON shape:
{{
  "name_ta": "Tamil recipe name",
  "name_en": "English recipe name",
  "short_description": "one short sentence",
  "ingredients": [
    {{"name_ta": "Tamil", "name_en": "English", "quantity": "quantity"}}
  ],
  "steps": ["step 1", "step 2"],
  "chef_tips": ["tip 1", "tip 2"],
  "optional_ingredients": ["item 1", "item 2"]
}}
"""

    try:
        response = ai.responses.create(
            model="gpt-5.6",
            input=prompt
        )
        recipe = extract_json(response.output_text)
        return {"ok": True, "recipe": recipe}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI recipe failed: {exc}")


@app.post("/api/ai/pantry-scan")
def pantry_scan(req: PantryScanRequest):
    ai = get_client()

    mime = req.mime_type if req.mime_type.startswith("image/") else "image/jpeg"

    try:
        # Validate base64 before sending it to the model.
        raw = base64.b64decode(req.image_base64, validate=True)
        if not raw:
            raise ValueError("Empty image.")
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("Image is too large. Please use an image under 8 MB.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image data.")

    data_url = f"data:{mime};base64,{req.image_base64}"

    prompt = """
Look at this kitchen/pantry image and identify visible cooking ingredients.

Return ONLY valid JSON in this exact shape:
{
  "items": [
    {
      "name_en": "English ingredient name",
      "name_ta": "Tamil ingredient name",
      "estimated_quantity": "visible estimate or unknown",
      "confidence_0_to_1": 0.0
    }
  ]
}

Rules:
- Include only ingredients you can reasonably identify.
- Do not identify people.
- Do not guess a brand or exact quantity when it is not visible.
- Keep confidence between 0 and 1.
- If nothing useful is visible, return {"items":[]}.
"""

    try:
        response = ai.responses.create(
            model="gpt-5.6",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )
        result = extract_json(response.output_text)
        items = result.get("items", [])
        if not isinstance(items, list):
            items = []
        return {"ok": True, "items": items}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Pantry scan failed: {exc}")


@app.get("/api/market-rates")
def market_rates(
    district: str = "Kallakurichi",
    q: str = "",
    category: str = ""
):
    # Deliberately do not fabricate prices.
    # A verified government/approved market-data connector can be added here later.
    return {
        "ok": False,
        "error": (
            f"Verified live market data is not configured for {district}. "
            "No fake price is returned."
        ),
        "district": district,
        "query": q,
        "category": category,
        "items": []
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
