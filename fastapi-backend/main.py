from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load credentials from the toolkit directory where they are securely stored
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "toolkit", ".env")
load_dotenv(dotenv_path)

from api.routers import jobs, tools, remy

app = FastAPI(title="PA AI Toolkit Backend API")

# Setup CORS for Vite React frontend
origins = [
    "http://localhost:5173", # Vite default port
    "http://127.0.0.1:5173",
    # Add production URL here later
]

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
