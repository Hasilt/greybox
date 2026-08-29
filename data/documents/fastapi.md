# FastAPI: Modern Async Web Framework

FastAPI is a high-performance Python web framework built on ASGI (Asynchronous Server Gateway Interface) that simplifies building REST APIs with automatic validation, documentation, and async support. It combines the simplicity of Flask with the performance of async frameworks like Starlette, making it ideal for data-intensive applications like RAG systems.

## ASGI Framework Foundation

FastAPI is built on Starlette, a lightweight ASGI framework. ASGI is the async counterpart to WSGI (Synchronous Server Gateway Interface), enabling non-blocking I/O. This means handlers can await database queries, HTTP calls, or external ML model invocations without blocking other requests. For RAG systems that frequently call embedding models or vector databases, async is essential for throughput.

A FastAPI application is an instance of the `FastAPI` class. The framework handles HTTP lifecycle management, routing, middleware chaining, and response serialization automatically.

## Path Operations and Routing

Path operations are functions that handle HTTP requests to specific routes. A simple path operation is decorated with a method (GET, POST, PUT, DELETE) and a path:

```python
@app.get("/query")
async def search(q: str):
    return {"query": q}
```

FastAPI automatically extracts query parameters, path parameters, request bodies, and headers. Path parameters are defined inline:

```python
@app.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    return {"doc_id": doc_id}
```

FastAPI validates that `doc_id` is an integer and returns a 422 error if not. This automatic validation reduces boilerplate and prevents common bugs.

## Pydantic Models and Request/Response Validation

Pydantic is a data validation library integrated deeply into FastAPI. Request and response bodies are defined as Pydantic models—dataclass-like objects that enforce type validation and serialize to JSON automatically.

```python
from pydantic import BaseModel

class EmbeddingQuery(BaseModel):
    text: str
    model: str = "bge-small-en-v1.5"
    normalize: bool = True

@app.post("/embed")
async def embed(query: EmbeddingQuery):
    return {"embedding": [...]}
```

Pydantic validates incoming JSON against the model schema. If the request is missing required fields or has incorrect types, FastAPI returns a detailed 422 validation error. Response models automatically serialize dataclass instances to JSON.

Optional fields are declared with `Optional[Type]` or `Union[Type, None]`. Default values are supported. Nested models allow composition of complex request/response structures.

## Dependency Injection

FastAPI's dependency injection system enables reusable components across path operations. Dependencies are functions that can themselves have dependencies, forming a directed acyclic graph.

```python
def get_database():
    # initialization
    return db

@app.get("/search")
async def search(q: str, db = Depends(get_database)):
    return db.query(q)
```

The `Depends()` function declares that the function depends on `get_database()`. FastAPI calls `get_database()`, passes its result to `search()`, and caches it within the request scope. Dependencies can be chained and shared across multiple path operations.

For RAG systems, dependencies often handle authentication, database connections, embedding model initialization, and vector store access. Scoping ensures resources are created once per request and properly cleaned up.

## Async Endpoints and Concurrency

Path operations are defined as `async def`, allowing non-blocking I/O:

```python
@app.post("/retrieve")
async def retrieve(query: str):
    embedding = await embedding_model.encode(query)
    results = await vector_db.search(embedding)
    return results
```

When the embedding model or vector database is queried, the request is suspended and the event loop processes other requests. This multiplexing enables high concurrency with a single thread.

Blocking I/O (e.g., database calls without async support) should be wrapped with `run_in_threadpool()` to avoid blocking the event loop.

## Automatic OpenAPI and Swagger Documentation

FastAPI generates OpenAPI (formerly Swagger) specifications automatically from type hints and Pydantic models. The Swagger UI is served at `/docs`, providing an interactive interface to test endpoints.

The OpenAPI spec is available at `/openapi.json` and can be imported into API testing tools like Postman or used for code generation. This eliminates the need for separate documentation maintenance.

## Startup and Shutdown Lifespan Events

The `lifespan` context manager enables initialization and cleanup logic:

```python
@app.on_event("startup")
async def startup():
    await initialize_embedding_model()
    await connect_vector_database()

@app.on_event("shutdown")
async def shutdown():
    await close_vector_database()
```

Startup events are called once when the application starts; shutdown events run before the server stops. This is critical for RAG systems: embedding models and vector databases are initialized once and shared across all requests.

## Routers and Modular Organization

Routers enable modular endpoint organization:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

@router.post("/retrieve")
async def retrieve(query: str):
    ...

app.include_router(router)
```

This creates endpoints like `/api/v1/retrieve`. Routers can be defined in separate modules and included in the main application, supporting clean separation of concerns as the API grows.

## Background Tasks

Background tasks allow handlers to return immediately while deferring work:

```python
from fastapi import BackgroundTasks

@app.post("/embed")
async def queue_embedding(url: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(embedding_worker, url)
    return {"status": "queued"}
```

Background tasks run after the response is sent. Useful for non-critical work like logging, index updates, or embedding cache refreshes that should not block user requests.

## Exception Handling and Middleware

FastAPI supports custom exception handlers and middleware for cross-cutting concerns:

```python
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.middleware("http")
async def log_middleware(request, call_next):
    response = await call_next(request)
    return response
```

Middleware processes all requests and responses. Common uses include timing requests, adding request IDs for tracing, and implementing rate limiting.

FastAPI's combination of async concurrency, automatic validation, and excellent DX makes it the standard choice for building production RAG backends.
