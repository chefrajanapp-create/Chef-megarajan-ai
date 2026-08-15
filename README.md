# Chef Megarajan AI — MASTER V1

The single source-of-truth project for the website/app.

Frontend:
`frontend/index.html`

Backend:
`backend/app.py`

Run frontend locally:
serve `frontend/` with a local HTTP server.

Run backend:
`uvicorn app:app --app-dir backend --reload`

Important:
- This is a development master, not yet a public production deployment.
- Never put an OpenAI API key in frontend files.
- Live market rates must come from a verified source; do not fabricate prices.
