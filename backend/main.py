# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # ✅ ADD THIS IMPORT
from fastapi.responses import HTMLResponse
import os

# ✅ Import the auth routes
from backend.routes import auth
from backend.routes import repositories

app = FastAPI(
    title="AI Migration Agent",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include the auth router
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(repositories.router, prefix="/api/repositories", tags=["Repositories"])

# ✅ MOUNT STATIC FILES - THIS IS THE KEY FIX!
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Simple HTML response function
def get_template_content(filename):
    try:
        with open(f"frontend/templates/{filename}", "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"<h1>Template not found: {filename}</h1>"

@app.get("/")
async def root():
    return {"message": "AI Migration Agent is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Server is running"}

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    content = get_template_content("login.html")
    return HTMLResponse(content=content)

@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    content = get_template_content("signup.html")
    return HTMLResponse(content=content)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    content = get_template_content("dashboard.html")
    return HTMLResponse(content=content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)