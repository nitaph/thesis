# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import scoring, generate

app = FastAPI(title="Creativity Study Backend", version="1.0.0")

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://*.qualtrics.com",
    "https://*.qualtrics.eu",
    "https://*.qualtrics.com/jfe",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.qualtrics\.(com|eu)$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

app.include_router(scoring.router, prefix="/api", tags=["scoring"])
app.include_router(generate.router, prefix="/api", tags=["generate"])
