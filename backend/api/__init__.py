"""
API Routers Package

This module aggregates all API routers for the application.
Each router handles a specific domain (auth, products, recommendations).
"""
from fastapi import APIRouter

# Re-export for convenience
from . import auth, products, recommendations

__all__ = ["auth", "products", "recommendations"]
