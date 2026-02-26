"""
Specialized Hubs API Routes

Handles the "Hub" specific pages (TCG, Retro, Comics).
These pages act as curated entry points with specific filters and layouts.
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.db import get_session
from api.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

HUB_CONFIG = {
    "tcg": {
        "title": "TCG Vault",
        "subtitle": "Pokémon, Magic, Yu-Gi-Oh!",
        "icon": "🃏",
        "filters": ["set", "rarity", "grading"],
        "hero_class": "hero-tcg"
    },
    "retro": {
        "title": "Retro Cave",
        "subtitle": "Nintendo, Sega, PlayStation",
        "icon": "🕹️",
        "filters": ["console", "region", "completeness"],
        "hero_class": "hero-retro"
    },
    "comics": {
        "title": "Comics Corner",
        "subtitle": "Manga, Marvel, Bonelli",
        "icon": "📚",
        "filters": ["publisher", "era", "first_edition"],
        "hero_class": "hero-comics"
    }
}

@router.get("/{category}", response_class=HTMLResponse)
async def get_hub(
    request: Request,
    category: str,
    user = Depends(get_current_user)
):
    """
    Render a specialized hub page.
    """
    config = HUB_CONFIG.get(category)
    if not config:
        # Fallback for unknown categories or redirect to search
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/products?category={category}")
    
    return templates.TemplateResponse(
        "hubs/hub.html",
        {
            "request": request,
            "category": category,
            "config": config,
            "user": user,
            "title": f"{config['title']} | Piranha ITA"
        }
    )
