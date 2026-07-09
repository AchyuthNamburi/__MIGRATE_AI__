# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Templates
templates = Jinja2Templates(directory="frontend/templates")

# ===== ROOT — ONLY ONE! =====
@app.get("/")
async def root():
    return {"message": "AI Migration Agent is running!"}

# ===== HEALTH =====
@app.get("/health")
async def health():
    return {"status": "healthy"}

# ===== PAGES =====
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ===== STARTUP =====
@app.on_event("startup")
async def startup():
    from backend.core.database import engine, Base
    from backend.models.user import User, UserProfile
    from backend.models.migration import MigrationJob, MigrationFile, MigrationReview, MigrationHistory
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")