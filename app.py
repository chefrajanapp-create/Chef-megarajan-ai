import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI

APP_NAME = "Chef Megarajan AI"
VERSION = "2.0.0"
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"

app = FastAPI(title=APP_NAME, version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")

SYSTEM_PROMPT = """
You are Chef Megarajan AI, a friendly Indian cooking assistant.
Help with Tamil, Tanglish and English recipes, cooking methods, ingredient
substitutions, quantities, nutrition, shopping lists, approximate costs,
meal planning, budget cooking and kitchen tips.

Reply in the language/style the user uses. Be friendly, practical and simple.
For recipes, give ingredients with quantities followed by clear cooking steps.
Nutrition and cost values are approximate unless a live verified source exists.
Do not invent live market prices or medical facts.
"""

class AskRequest(BaseModel):
    message: str

@app.get("/")
def home():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return {"name": APP_NAME, "version": VERSION, "status": "live"}

@app.get("/api/health")
def health():
    return {"ok": True, "service": "chef-megarajan-ai", "version": VERSION}

@app.get("/api/status")
def status():
    return {
        "recipes": "ready",
        "nutrition": "ready",
        "shopping": "ready",
        "pantry": "ready",
        "ai": "ready" if client else "missing OPENAI_API_KEY",
        "market": "price source not connected"
    }

def ask_chef(request: AskRequest):
    message = request.message.strip()

    if not message:
        return {"ok": False, "answer": "👨‍🍳 என்ன சமைக்கணும் அல்லது என்ன தெரிஞ்சிக்கணும்? கேளுங்க!"}

    if client is None:
        return {"ok": False, "answer": "⚠️ OpenAI API key connect ஆகவில்லை. Render Environment Variables-ல் OPENAI_API_KEY check பண்ணுங்க."}

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=message
        )
        return {"ok": True, "answer": response.output_text, "model": MODEL}
    except Exception as error:
        print("OpenAI error:", error)
        return {"ok": False, "answer": "⚠️ AI Chef-ஐ connect செய்யும்போது ஒரு பிரச்சனை ஏற்பட்டது. சிறிது நேரம் கழித்து மீண்டும் முயற்சி செய்யுங்கள்."}

@app.post("/api/ask")
def api_ask(request: AskRequest):
    return ask_chef(request)

@app.post("/api/chat")
def chat(request: AskRequest):
    return ask_chef(request)

@app.post("/api/recipe")
def recipe(request: AskRequest):
    prompt = f"""Create a practical cooking recipe for:
{request.message}

Give:
1. Recipe name
2. Ingredients with quantities
3. Preparation
4. Cooking steps
5. Cooking tips
6. Approximate serving size
"""
    return ask_chef(AskRequest(message=prompt))

@app.post("/api/nutrition")
def nutrition(request: AskRequest):
    prompt = f"""Give approximate nutrition information for:
{request.message}

Include calories if reasonably possible, protein, carbohydrates, fat,
useful nutrients, and simple health notes. Clearly say values are approximate.
"""
    return ask_chef(AskRequest(message=prompt))

@app.post("/api/shopping")
def shopping(request: AskRequest):
    prompt = f"""Create a practical shopping list for:
{request.message}

Give ingredient, approximate quantity, optional substitute, and checklist format.
"""
    return ask_chef(AskRequest(message=prompt))

@app.post("/api/cost")
def cost(request: AskRequest):
    prompt = f"""Estimate the cooking cost for:
{request.message}

Give ingredient, approximate quantity, approximate cost and total approximate cost.
Prices vary by location and date. Do not claim these are live market prices.
"""
    return ask_chef(AskRequest(message=prompt))

@app.on_event("startup")
def startup_event():
    print("CHEF MEGARAJAN AI -", "AI CONNECTION READY" if client else "OPENAI_API_KEY NOT FOUND")
