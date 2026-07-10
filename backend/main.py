# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import os

# ✅ Import the routers
from backend.routes import auth, repositories

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

# ✅ Register the routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(repositories.router, prefix="/api/repositories", tags=["Repositories"])

# ===== SIMPLE HTML LOADER =====
def load_html(filename: str) -> str:
    try:
        with open(f"frontend/templates/{filename}", "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"<h1>Template not found: {filename}</h1>"

# ===== ROOT =====
@app.get("/")
async def root():
    return RedirectResponse(url="/login")

# ===== HEALTH =====
@app.get("/health")
async def health():
    return {"status": "healthy"}

# ===== PAGES =====
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=load_html("login.html"))

@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    return HTMLResponse(content=load_html("signup.html"))

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return HTMLResponse(content=load_html("dashboard.html"))

# ===== STARTUP =====
@app.on_event("startup")
async def startup():
    try:
        from backend.core.database import engine, Base
        from backend.models.user import User, UserProfile
        from backend.models.migration import MigrationJob, MigrationFile, MigrationReview, MigrationHistory
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️ Database startup error: {e}")