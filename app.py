from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Chef Megarajan AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to the production domain before launch.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"ok": True, "service": "chef-megarajan-ai", "version": "1.0.0"}

@app.get("/api/status")
def status():
    return {
        "recipes": "frontend dataset ready",
        "nutrition": "frontend dataset ready",
        "shopping": "ready",
        "pantry": "ready",
        "ai": "connect server-side OpenAI key here",
        "market": "connect verified Tamil Nadu price source here",
    }
