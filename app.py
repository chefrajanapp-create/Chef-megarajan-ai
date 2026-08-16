import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"

app = FastAPI(
    title="Chef Megarajan AI API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str | None = None
    message: str | None = None
    query: str | None = None
    text: str | None = None


def get_question(data: AskRequest) -> str:
    value = data.question or data.message or data.query or data.text or ""
    return value.strip()


def get_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    if OpenAI is None:
        raise HTTPException(
            status_code=500,
            detail="OpenAI Python package is missing. Add 'openai' to requirements.txt and redeploy.",
        )

    return OpenAI(api_key=api_key)


@app.get("/")
def home():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return {
        "service": "chef-megarajan-ai",
        "ok": True,
        "message": "Backend is running. index.html was not found in the server directory.",
    }


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "chef-megarajan-ai",
        "version": "2.0.0",
        "openai_key_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    }


@app.get("/api/status")
def status():
    key_ready = bool(os.getenv("OPENAI_API_KEY", "").strip())
    return {
        "recipes": "frontend dataset ready",
        "nutrition": "frontend dataset ready",
        "shopping": "ready",
        "pantry": "ready",
        "ai": "ready" if key_ready else "OPENAI_API_KEY not configured",
        "market": "connect verified Tamil Nadu price source here",
    }


@app.post("/api/ask")
@app.post("/ask")
def ask(data: AskRequest):
    question = get_question(data)

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please send a question.",
        )

    # Keep requests reasonably small and prevent accidental huge payloads.
    question = question[:6000]

    client = get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6").strip() or "gpt-5.6"

    instructions = """
You are Chef Megarajan AI, a practical cooking assistant.

Answer the user's cooking, recipe, ingredient, kitchen, nutrition, shopping,
or food-cost questions clearly and helpfully.

The user may write in Tamil, Tanglish, or English.
Reply in the same language/style when practical.
For recipes, give ingredients and clear step-by-step preparation.
For quantities, use practical kitchen measurements.
Do not invent live market prices. If a current price is requested and no
verified price data is available, clearly say that a live verified price
source is not connected yet.

Keep answers concise unless the user asks for detailed instructions.
"""

    try:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=question,
        )

        answer = (response.output_text or "").strip()

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="OpenAI returned an empty response.",
            )

        return {
            "ok": True,
            "answer": answer,
            "response": answer,
            "model": model,
        }

    except HTTPException:
        raise
    except Exception as exc:
        # Do not expose the API key or internal credentials.
        raise HTTPException(
            status_code=502,
            detail=f"AI request failed: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
