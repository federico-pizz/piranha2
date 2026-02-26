"""
Authentication API Routes

Handles user registration, login, logout, and profile management.
Uses JWT tokens stored in HTTP-only cookies for security.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pathlib import Path

from config import get_settings
from models.user import UserCreate, User, LoginRequest, Token
from services.db import get_session, User as DBUser

router = APIRouter()
TEMPLATES_DIR = str(Path(__file__).resolve().parent.parent.parent / "frontend" / "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def get_db():
    """Database session dependency."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[DBUser]:
    """
    Dependency to get current user from JWT cookie.
    Returns None if not authenticated (for optional auth).
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    
    user = db.query(DBUser).filter(DBUser.email == email).first()
    return user


async def require_auth(request: Request, db: Session = Depends(get_db)) -> DBUser:
    """Dependency that requires authentication."""
    user = await get_current_user(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"HX-Redirect": "/auth/login"},
        )
    return user


# ============== HTML Pages ==============

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render registration page."""
    return templates.TemplateResponse("auth/register.html", {"request": request})


# ============== API Endpoints ==============

@router.post("/register")
async def register(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    form = await request.form()
    email = form.get("email")
    password = form.get("password")
    
    # Check if user exists
    existing = db.query(DBUser).filter(DBUser.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = DBUser(
        email=email,
        password_hash=get_password_hash(password),
        preferences={}
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token and set cookie
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.debug,
        samesite="strict",
        max_age=settings.access_token_expire_minutes * 60
    )
    return response


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    form = await request.form()
    email = form.get("email")
    password = form.get("password")
    
    user = db.query(DBUser).filter(DBUser.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.debug,
        samesite="strict",
        max_age=settings.access_token_expire_minutes * 60
    )
    return response


@router.post("/logout")
async def logout(response: Response):
    """Clear authentication cookie."""
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@router.get("/me")
async def get_me(user: DBUser = Depends(require_auth)):
    """Get current user information."""
    return {
        "id": str(user.id),
        "email": user.email,
        "preferences": user.preferences,
        "created_at": user.created_at.isoformat()
    }
