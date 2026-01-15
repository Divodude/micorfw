# MicroFW Framework Framework Documentation

MicroFW is a lightweight, asynchronous microservices framework for Python, designed for speed and simplicity. It relies on ASGI and provides built-in support for service discovery, middleware, and dependency injection.

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Routing & Handlers](#routing--handlers)
5. [Middleware](#middleware)
6. [Database Integration](#database-integration)
7. [Service Registry & Client](#service-registry--client)
8. [Lifecycle Events](#lifecycle-events)

---

## Installation & Setup

MicroFW requires Python 3.8+ and an ASGI server (like `uvicorn`) to run.

**Dependencies:**
- `uvicorn`: ASGI server
- `pydantic`: Data validation (optional but recommended)
- `sqlalchemy` & `aiosqlite`: Database capabilities

**Directory Structure:**
```
project/
├── main.py           # Entry point
├── microfw/          # Framework core
└── requirements.txt
```

---

## Quick Start

Create a `main.py` file to initialize your application:

```python
from microfw.app import App
from microfw.response import Response
from microfw.asgi import ASGI

app = App()

# Simple GET Route
@app.route("/", methods=["GET"])
def index():
    return Response("Hello, MicroFW!", status_code=200)

# Expose as ASGI app
asgi = ASGI(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:asgi", port=8000, reload=True)
```

Run with: `uvicorn main:asgi --reload`

---

## Configuration

MicroFW avoids global configuration files. Instead, configuration is handled programmatically during the `App` initialization or via environment variables loaded by your application.

### Service Registry Configuration
Register other microservices for service-to-service communication:

```python
app = App()
app.add_service("user-service", "http://localhost:8001")
app.add_service("payment-service", "http://localhost:8002")
```

---

## Routing & Handlers

MicroFW supports function-based views with dependency injection.

### Path Parameters
Use `{var_name}` syntax in routes. The framework automatically parses them.

```python
@app.route("/users/{user_id}", methods=["GET"])
async def get_user(user_id):
    return Response(f"User ID: {user_id}")
```

### Request Body & Pydantic
If `pydantic` is installed, simply type-hint a parameter with a Pydantic model to have the body automatically parsed and validated.

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

@app.route("/users", methods=["POST"])
async def create_user(user_data: UserCreate):
    # user_data is already a validated UserCreate instance
    return Response({"id": 123, "name": user_data.name}, status_code=201)
```

### Accessing the Request Object
Add `request` as a parameter to any handler to access the raw request object (headers, query params, etc.).

```python
@app.route("/search")
async def search(request):
    query = request.query  # Raw query string
    method = request.method
    return Response(f"Searching for {query}")
```

---

## Middleware

Middleware wraps the request handling pipeline. It works similarly to other ASGI frameworks but with a simpler interface.

### Adding Middleware
```python
from microfw.middleware.concurrency import ConcurrencyMiddleware

# Add middleware (executed in reverse order of addition - LIFO)
app.middleware(ConcurrencyMiddleware(limit=100))
```

### Writing Custom Middleware
Middleware functions (or callables) receive `request` and `call_next`.

```python
async def simple_logging_middleware(request, call_next):
    print(f"Incoming: {request.method} {request.path}")
    response = await call_next(request)
    print(f"Outgoing status: {response.status_code}")
    return response

app.middleware(simple_logging_middleware)
```

---

## Database Integration

MicroFW has built-in support for SQLAlchemy (async).

### Setup
```python
from microfw.orm_db import Database
from microfw.middleware.db import DatabaseMiddleware
from microfw.middleware.transaction import TransactionMiddleware

# 1. Initialize DB
db = Database("sqlite+aiosqlite:///app.db")

# 2. Add Middlewares (Order matters!)
app.middleware(DatabaseMiddleware(db))       # Injects `request.db` session
app.middleware(TransactionMiddleware())      # Handles commit/rollback automatically
```

### Usage in Handlers
Access the session via `request.db`.

```python
from sqlalchemy import select

@app.route("/items")
async def list_items(request):
    result = await request.db.execute(select(Item))
    items = result.scalars().all()
    return Response([{"name": i.name} for i in items])
```

---

## Service Registry & Client

For microservices, use `ServiceClient` to make internal requests with context propagation (Trace IDs, Deadlines).

### Usage
The `ServiceClient` is typically initialized with the current request context.

```python
from microfw.client import ServiceClient

@app.route("/proxy-request")
async def proxy_handler(request):
    # Access the service registry from the app (via request context if available, or global app)
    # Typically, you would instantiate the client using the current request context
    
    # Assuming access to app.services
    client = ServiceClient(request.context, app.services)
    
    # Make a call to 'user-service' (must be registered)
    try:
        response = await client.get("user-service", "/users/1")
        return Response(response.json())
    except HTTPException as e:
        return Response(e.detail, status_code=e.status_code)
```

**Features:**
*   **Service Discovery**: Resolves `user-service` to its base URL.
*   **Trace Propagation**: Automatically forwards `X-Trace-ID` and `X-Parent-Span` headers.
*   **Timeout Handling**: Enforces request deadlines.

---

## Lifecycle Events

Hook into application startup and shutdown.

```python
@app.on_event("startup")
async def startup_db():
    await db.connect()

@app.on_event("shutdown")
async def shutdown_db():
    await db.disconnect()
```
