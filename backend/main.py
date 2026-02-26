"""
Piranha ITA - FastAPI Application Entry Point

This is the main application that ties together all components:
- Jinja2 templates for server-side rendering
- HTMX endpoints for dynamic updates
- REST API for data operations
- Static file serving
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

from config import get_settings
from api import auth, products, recommendations, hubs
from services.db import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager - runs on startup and shutdown.
    Creates database tables if they don't exist.
    """
    create_tables()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Privacy-focused used goods comparison engine for Italian marketplaces",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - configure for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates directory
templates = Jinja2Templates(directory="templates")

# Static files (CSS, JS, images)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(hubs.router, prefix="/hubs", tags=["Hubs"])


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing page - renders the home template."""
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "title": "Piranha ITA"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {"status": "healthy", "service": "piranha-web"}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """User dashboard - redirects to recommendations dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/recommendations/dashboard", status_code=302)


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Admin panel (placeholder for now)."""
    # In a real app, add auth dependency here!
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About us page."""
    return templates.TemplateResponse("about.html", {"request": request})
