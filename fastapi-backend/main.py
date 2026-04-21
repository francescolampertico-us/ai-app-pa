from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load credentials: try toolkit/.env for local dev; production uses platform env vars
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "toolkit", ".env")
load_dotenv(dotenv_path, override=False)

from api.routers import jobs, tools, remy

app = FastAPI(title="PA AI Toolkit Backend API")

# CORS origins: always allow common localhost dev ports; extend via CORS_ORIGINS env var (comma-separated).
_extra = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
_default_origins = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:4175",
    "http://127.0.0.1:4175",
}
origins = list(_default_origins | set(_extra))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(remy.router, prefix="/api/remy", tags=["Remy"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
