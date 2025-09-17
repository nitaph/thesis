from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import admin
from app.config import settings
from app.db import init_db
from app.routes import scoring, personas, generate, ratings, export

app = FastAPI(title="Creativity Study Backend", version="1.0.0")

# CORS — restrict to Qualtrics + localhost for dev
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

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(admin.router,   prefix="/api", tags=["admin"])
app.include_router(scoring.router, prefix="/api", tags=["scoring"])
app.include_router(personas.router, prefix="/api", tags=["personas"])
app.include_router(generate.router, prefix="/api", tags=["generate"])
app.include_router(ratings.router,  prefix="/api", tags=["ratings"])
app.include_router(export.router,    prefix="/api", tags=["export"])
