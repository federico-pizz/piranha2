# Backend - Learning Guide

This folder contains the FastAPI web application. Here's how everything fits together.

## 📁 Folder Structure

```
backend/
├── main.py          # Application entry point
├── config.py        # Environment settings
├── api/             # API route handlers
├── models/          # Pydantic data models
├── services/        # Database & business logic
├── templates/       # Jinja2 HTML templates
└── static/          # CSS and static assets
```

## 🔧 Key Concepts

### 1. FastAPI Basics

FastAPI is a modern Python web framework. Key features:

```python
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

- **Type hints** → Automatic validation and docs
- **Async/await** → Non-blocking I/O
- **Automatic OpenAPI** → Visit `/docs` for API explorer

### 2. Dependency Injection

FastAPI uses `Depends()` for reusable dependencies:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

### 3. Pydantic Models

Data validation and serialization:

```python
from pydantic import BaseModel

class User(BaseModel):
    email: str
    name: str
    
# Automatic validation
user = User(email="test@example.com", name="John")
```

### 4. Jinja2 Templates

Server-side rendering:

```python
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html", 
        {"request": request, "title": "Home"}
    )
```

## 🔒 Authentication Flow

1. User submits login form
2. Backend verifies password with bcrypt
3. JWT token created and stored in HTTP-only cookie
4. Subsequent requests include cookie automatically
5. `require_auth` dependency validates token

## 📚 Files Explained

| File | Purpose |
|------|---------|
| `main.py` | App initialization, middleware, routers |
| `config.py` | Environment variables with Pydantic Settings |
| `api/auth.py` | Login, register, logout endpoints |
| `api/products.py` | Product CRUD and search |
| `api/recommendations.py` | ML-powered recommendations |
| `services/db.py` | SQLAlchemy models and session |
| `models/user.py` | Pydantic request/response schemas |

## 🧪 Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload --port 8000

# Access API docs
open http://localhost:8000/docs
```

## 💡 Tips

- Use `async def` for I/O-bound operations
- Add type hints everywhere for better IDE support
- Check `/docs` for auto-generated API documentation
- Use `Depends()` to share logic between endpoints
