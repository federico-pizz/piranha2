# Templates - Learning Guide

This folder contains Jinja2 templates enhanced with HTMX and Alpine.js for a dynamic, no-framework frontend.

## 🔧 Key Technologies

### Jinja2 (Server-Side Rendering)

Jinja2 renders HTML on the server before sending to the browser.

```html
<!-- Template syntax -->
<h1>{{ title }}</h1>

{% for product in products %}
    <div>{{ product.name }} - €{{ product.price }}</div>
{% endfor %}

{% if user %}
    <p>Welcome, {{ user.name }}</p>
{% endif %}
```

### HTMX (Dynamic Updates Without JavaScript)

HTMX adds interactivity via HTML attributes:

```html
<!-- Load content on click -->
<button hx-get="/products" hx-target="#results">
    Load Products
</button>

<!-- Infinite scroll -->
<div hx-get="/products?page=2" 
     hx-trigger="revealed" 
     hx-swap="beforeend">
    Loading more...
</div>

<!-- Form submission without reload -->
<form hx-post="/auth/login" hx-target="#message">
    <input name="email" type="email">
    <button>Login</button>
</form>
```

Key HTMX attributes:
- `hx-get/post/put/delete` → HTTP method and URL
- `hx-target` → Where to put the response
- `hx-trigger` → When to fire (click, load, revealed)
- `hx-swap` → How to insert (innerHTML, beforeend, outerHTML)

### Alpine.js (Lightweight Reactivity)

Alpine.js handles client-side state without a build step:

```html
<!-- Toggle visibility -->
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">Hidden content</div>
</div>

<!-- Form validation -->
<form x-data="{ email: '', valid: false }">
    <input x-model="email" 
           @input="valid = email.includes('@')">
    <button :disabled="!valid">Submit</button>
</form>

<!-- Dark mode -->
<body x-data="{ dark: false }" :class="{ 'dark': dark }">
    <button @click="dark = !dark">Toggle Theme</button>
</body>
```

Key Alpine.js directives:
- `x-data` → Initialize component state
- `x-show` → Toggle visibility
- `x-model` → Two-way binding (like v-model)
- `@click` → Event handlers
- `:class` → Dynamic classes

## 📁 Template Structure

```
templates/
├── base.html              # Layout with nav, footer
├── home.html              # Landing page
├── dashboard.html         # User dashboard
├── auth/
│   ├── login.html         # Login form
│   └── register.html      # Registration form
├── products/
│   ├── list.html          # Product grid
│   ├── _list_items.html   # HTMX partial (items only)
│   └── detail.html        # Single product
└── recommendations/
    └── list.html          # Personalized recs
```

### Partial Templates (HTMX Pattern)

Files starting with `_` are partials for HTMX requests:

```python
# In the API
if request.headers.get("HX-Request"):
    # Return just the items
    return templates.TemplateResponse("products/_list_items.html", ...)
else:
    # Return full page
    return templates.TemplateResponse("products/list.html", ...)
```

## 💡 Best Practices

1. **Extend base.html** - Don't repeat nav/footer
   ```html
   {% extends "base.html" %}
   {% block content %}...{% endblock %}
   ```

2. **Use partials for HTMX** - Keep them small and focused

3. **Combine HTMX + Alpine.js** - HTMX for server data, Alpine for UI state

4. **Progressive enhancement** - Works without JS, enhanced with HTMX

## 🎨 CSS Variables

See `static/css/main.css` for the design system:

```css
:root {
    --color-primary: #2563eb;
    --color-bg: #ffffff;
    --space-md: 1rem;
}

.dark {
    --color-bg: #0f172a;
}
```

## 📚 Resources

- [Jinja2 Docs](https://jinja.palletsprojects.com/)
- [HTMX Docs](https://htmx.org/docs/)
- [Alpine.js Docs](https://alpinejs.dev/start-here)
