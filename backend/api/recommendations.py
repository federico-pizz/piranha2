"""
Recommendations API Routes

Handles personalized product recommendations for users.
Uses Redis caching for fast response times.
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
import redis
import json

from config import get_settings
from services.db import get_session, Product as DBProduct, Recommendation as DBRecommendation
from services.db import User as DBUser
from api.auth import get_current_user, require_auth

router = APIRouter()
TEMPLATES_DIR = str(Path(__file__).resolve().parent.parent.parent / "frontend" / "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
settings = get_settings()


def get_db():
    """Database session dependency."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Redis connection for caching."""
    try:
        return redis.from_url(settings.redis_url)
    except:
        return None


@router.get("", response_class=HTMLResponse)
async def get_recommendations(
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(require_auth),
    limit: int = 12,
):
    """
    Get personalized recommendations for the current user.
    Uses cached results if available.
    """
    cache = get_redis()
    cache_key = f"recommendations:{user.id}"
    
    # Try cache first
    if cache:
        cached = cache.get(cache_key)
        if cached:
            product_ids = json.loads(cached)
            products = db.query(DBProduct).filter(DBProduct.id.in_(product_ids)).all()
            
            if request.headers.get("HX-Request"):
                return templates.TemplateResponse(
                    "recommendations/_items.html",
                    {"request": request, "products": products}
                )
            
            return templates.TemplateResponse(
                "recommendations/list.html",
                {"request": request, "products": products, "user": user}
            )
    
    # Get from database (pre-computed recommendations)
    recommendations = db.query(DBRecommendation) \
        .filter(DBRecommendation.user_id == user.id) \
        .order_by(DBRecommendation.score.desc()) \
        .limit(limit) \
        .all()
    
    product_ids = [str(r.product_id) for r in recommendations]
    products = db.query(DBProduct).filter(DBProduct.id.in_(product_ids)).all()
    
    # Cache for 5 minutes
    if cache and product_ids:
        cache.setex(cache_key, 300, json.dumps(product_ids))
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "recommendations/_items.html",
            {"request": request, "products": products}
        )
    
    return templates.TemplateResponse(
        "recommendations/list.html",
        {"request": request, "products": products, "user": user}
    )


@router.post("/feedback")
async def submit_feedback(
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(require_auth),
):
    """
    Submit feedback (like/dislike) for a product.
    Used to improve recommendation accuracy.
    """
    form = await request.form()
    product_id = form.get("product_id")
    feedback_type = form.get("type")  # "like" or "dislike"
    
    if not product_id or feedback_type not in ["like", "dislike"]:
        raise HTTPException(status_code=400, detail="Invalid feedback data")
    
    # Store feedback in user preferences
    preferences = user.preferences or {}
    
    if "liked_products" not in preferences:
        preferences["liked_products"] = []
    if "disliked_products" not in preferences:
        preferences["disliked_products"] = []
    
    if feedback_type == "like":
        if product_id not in preferences["liked_products"]:
            preferences["liked_products"].append(product_id)
        # Remove from disliked if present
        if product_id in preferences["disliked_products"]:
            preferences["disliked_products"].remove(product_id)
    else:
        if product_id not in preferences["disliked_products"]:
            preferences["disliked_products"].append(product_id)
        # Remove from liked if present
        if product_id in preferences["liked_products"]:
            preferences["liked_products"].remove(product_id)
    
    user.preferences = preferences
    db.commit()
    
    # Invalidate cache
    cache = get_redis()
    if cache:
        cache.delete(f"recommendations:{user.id}")
    
    # Return updated button state (for HTMX)
    return HTMLResponse(
        content=f'<span class="feedback-success">Feedback recorded!</span>',
        status_code=200
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: DBUser = Depends(require_auth),
):
    """User dashboard with recommendations and preferences."""
    # Get recent recommendations
    recommendations = db.query(DBRecommendation) \
        .filter(DBRecommendation.user_id == user.id) \
        .order_by(DBRecommendation.score.desc()) \
        .limit(6) \
        .all()
    
    product_ids = [r.product_id for r in recommendations]
    products = db.query(DBProduct).filter(DBProduct.id.in_(product_ids)).all() if product_ids else []
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "recommendations": products,
            "preferences": user.preferences or {}
        }
    )
