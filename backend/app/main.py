# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="frontend/templates")

# Setup static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/dashboard")
async def dashboard(request: Request):
    """Serve the dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    """Serve login page"""
    return templates.TemplateResponse("login.html", {"request": request})