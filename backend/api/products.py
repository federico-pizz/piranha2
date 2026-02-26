"""
Products API Routes

Handles product listing, filtering, and comparison.
Supports HTMX partial rendering for infinite scroll.
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from services.db import get_session, Product as DBProduct
from api.auth import get_current_user
from services.db import User as DBUser

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    """Database session dependency."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_class=HTMLResponse)
async def list_products(
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[DBUser] = Depends(get_current_user),
    # Filters
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    condition: Optional[str] = None,
    region: Optional[str] = None,
    search: Optional[str] = None,
    # Hub Specific Filters (Metadata)
    set_name: Optional[str] = Query(None, alias="set"),
    rarity: Optional[str] = None,
    grading: Optional[str] = None,
    console: Optional[str] = None,
    completeness: Optional[str] = None,
    publisher: Optional[str] = None,
    era: Optional[str] = None,
    # Pagination
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=50),
):
    """
    List products with filtering and pagination.
    Returns full page or partial (for HTMX infinite scroll).
    """
    query = db.query(DBProduct)
    
    # Apply filters
    if category:
        query = query.filter(DBProduct.category == category)
    if brand:
        query = query.filter(DBProduct.brand.ilike(f"%{brand}%"))
    if min_price is not None:
        query = query.filter(DBProduct.price_eur >= min_price)
    if max_price is not None:
        query = query.filter(DBProduct.price_eur <= max_price)
    if condition:
        query = query.filter(DBProduct.condition == condition)
    if region:
        query = query.filter(DBProduct.region == region)
    if search:
        query = query.filter(
            or_(
                DBProduct.title.ilike(f"%{search}%"),
                DBProduct.description.ilike(f"%{search}%")
            )
        )
    

    
    # Apply Metadata Filters
    if set_name:
        query = query.filter(DBProduct.metadata_["set"].astext == set_name)
    if rarity:
        query = query.filter(DBProduct.metadata_["rarity"].astext == rarity)
    if grading:
        query = query.filter(DBProduct.metadata_["grading"].astext == grading)
    if console:
        query = query.filter(DBProduct.metadata_["console"].astext == console)
    if completeness:
        query = query.filter(DBProduct.metadata_["completeness"].astext == completeness)
    if publisher:
        query = query.filter(DBProduct.metadata_["publisher"].astext == publisher)
    if era:
        query = query.filter(DBProduct.metadata_["era"].astext == era)

    # Get total count for pagination
    total = query.count()
    
    # Order by newest first and paginate
    products = query.order_by(DBProduct.scraped_at.desc()) \
                    .offset((page - 1) * per_page) \
                    .limit(per_page) \
                    .all()
    
    has_more = (page * per_page) < total
    
    # Check if HTMX request (partial render)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "products/_list_items.html",
            {
                "request": request,
                "products": products,
                "page": page,
                "has_more": has_more,
            }
        )
    
    # Full page render
    return templates.TemplateResponse(
        "products/list.html",
        {
            "request": request,
            "products": products,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": has_more,
            "user": user,
            # Pass current filters for form state
            "filters": {
                "category": category,
                "brand": brand,
                "min_price": min_price,
                "max_price": max_price,
                "condition": condition,
                "region": region,
                "search": search,
                "set": set_name,
                "rarity": rarity,
                "console": console,
            }
        }
    )


# NOTE: /compare must come BEFORE /{product_id} so FastAPI doesn't try to parse "compare" as a UUID
@router.get("/compare", response_class=HTMLResponse)
async def compare_products(
    request: Request,
    ids: str = Query(..., description="Comma-separated product IDs"),
    db: Session = Depends(get_db),
    user: Optional[DBUser] = Depends(get_current_user),
):
    """
    Compare multiple products side-by-side.
    Accepts comma-separated UUIDs.
    """
    product_ids = [UUID(id.strip()) for id in ids.split(",") if id.strip()]
    
    if len(product_ids) < 2:
        return templates.TemplateResponse(
            "errors/400.html",
            {"request": request, "message": "Need at least 2 products to compare"},
            status_code=400
        )
    
    if len(product_ids) > 4:
        product_ids = product_ids[:4]  # Limit to 4 for UI
    
    products = db.query(DBProduct).filter(DBProduct.id.in_(product_ids)).all()
    
    return templates.TemplateResponse(
        "products/compare.html",
        {"request": request, "products": products, "user": user}
    )


@router.get("/{product_id}", response_class=HTMLResponse)
async def get_product(
    request: Request,
    product_id: UUID,
    db: Session = Depends(get_db),
    user: Optional[DBUser] = Depends(get_current_user),
):
    """Get single product details."""
    product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    
    if not product:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Product not found"},
            status_code=404
        )
    
    return templates.TemplateResponse(
        "products/detail.html",
        {"request": request, "product": product, "user": user}
    )
