# FastAPI - Web Framework

## What is FastAPI?

FastAPI is a modern Python web framework for building APIs. It's called "Fast" for two reasons:
1. **Fast to run**: One of the fastest Python frameworks (on par with Node.js/Go)
2. **Fast to code**: Type hints enable autocomplete, validation, and documentation

### Why FastAPI?

- **Automatic API docs** at `/docs` (Swagger UI)
- **Type validation** with Pydantic
- **Async support** for high concurrency
- **Dependency injection** for clean code
- **Easy testing** with TestClient

---

## Project Structure

```
backend/
├── main.py              # App entry point, middleware
├── api/                 # Route handlers
│   ├── auth.py          # Login, register, logout
│   ├── products.py      # Product listing, search, compare
│   └── recommendations.py
├── services/            # Business logic
│   ├── db.py            # Database models, sessions
│   └── recommendations.py
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── home.html
│   └── products/
├── static/              # CSS, JS, images
│   └── css/main.css
└── requirements.txt
```

---

## Core Concepts

### 1. Routes (Endpoints)

```python
from fastapi import APIRouter

router = APIRouter()

# GET request
@router.get("/products")
async def list_products():
    return {"products": [...]}

# With path parameter
@router.get("/products/{product_id}")
async def get_product(product_id: str):
    return {"id": product_id}

# POST request
@router.post("/products")
async def create_product(data: ProductCreate):
    return {"created": True}
```

### 2. Query Parameters

```python
@router.get("/products")
async def list_products(
    category: str = None,      # Optional
    min_price: float = 0,      # With default
    page: int = Query(1, ge=1) # With validation
):
    # category, min_price, page are automatically parsed from URL
    # /products?category=auto&min_price=100&page=2
    pass
```

### 3. Request Body (Pydantic Models)

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        # Example for docs
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "secretpassword"
            }
        }

@router.post("/register")
async def register(user: UserCreate):
    # user.email and user.password are validated
    pass
```

### 4. Dependency Injection

```python
from fastapi import Depends

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Use in route
@router.get("/products")
async def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

# Auth dependency
async def get_current_user(token: str = Cookie(None)):
    if not token:
        return None
    return verify_token(token)

@router.get("/profile")
async def profile(user: User = Depends(get_current_user)):
    return user
```

### 5. HTML Templates (Jinja2)

```python
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "title": "Home"}
    )
```

---

## HTMX Integration

We use HTMX for dynamic pages without JavaScript:

### Backend Detection
```python
@router.get("/products")
async def list_products(request: Request):
    products = get_products()
    
    # Check if HTMX request (partial update)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "products/_list_items.html",  # Partial template
            {"request": request, "products": products}
        )
    
    # Full page render
    return templates.TemplateResponse(
        "products/list.html",
        {"request": request, "products": products}
    )
```

### Template with HTMX
```html
<!-- Trigger on form change, update target -->
<form hx-get="/products" 
      hx-target="#products-grid" 
      hx-trigger="change">
    <select name="category">
        <option value="">All</option>
        <option value="auto">Auto</option>
    </select>
</form>

<div id="products-grid">
    {% include "products/_list_items.html" %}
</div>
```

---

## Authentication Flow

### 1. Registration
```
POST /auth/register
Body: {email, password}
→ Hash password
→ Create user in DB
→ Set JWT cookie
→ Redirect to home
```

### 2. Login
```
POST /auth/login
Body: {email, password}
→ Find user by email
→ Verify password hash
→ Create JWT token
→ Set HTTP-only cookie
→ Redirect to home
```

### 3. Protected Routes
```python
@router.get("/dashboard")
async def dashboard(user: User = Depends(require_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return templates.TemplateResponse(...)
```

---

## API Documentation

FastAPI generates interactive docs automatically:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Testing

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "Piranha" in response.text

def test_products():
    response = client.get("/products")
    assert response.status_code == 200
```

Run tests:
```bash
sudo docker exec -it piranha2-web-1 pytest
```

---

## Common Patterns

### Error Handling
```python
from fastapi import HTTPException

@router.get("/products/{id}")
async def get_product(id: str, db: Session = Depends(get_db)):
    product = db.query(Product).get(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
```

### Background Tasks
```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Slow operation
    pass

@router.post("/contact")
async def contact(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, message)
    return {"status": "Message queued"}
```

### File Uploads
```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    # Save file...
    return {"filename": file.filename}
```

---

## Development Commands

```bash
# Start with auto-reload (already configured in Docker)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Check routes
sudo docker exec -it piranha2-web-1 python -c "from main import app; print([r.path for r in app.routes])"

# View logs
sudo docker logs piranha2-web-1 -f
```

---

## Troubleshooting

### Template Not Found
```
jinja2.exceptions.TemplateNotFound: products/list.html
```
Check that template path is correct and file exists in `templates/` directory.

### 422 Unprocessable Entity
Request body doesn't match Pydantic model. Check:
- Required fields are present
- Field types are correct
- JSON is valid

### 500 Internal Server Error
```bash
# Check logs for traceback
sudo docker logs piranha2-web-1 --tail 50
```
