from contextlib import asynccontextmanager
from app.core.logging import get_logger
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from fastapi.responses import JSONResponse
from app.db.database import engine
from app.db import models
from app.api import users, partner_requests

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("Starting up the application...")
    # Create database tables
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    yield
    # Shutdown code
    logger.info("Shutting down the application...")

app = FastAPI(
    title="Dealnest Assessment API",
    description="An API for managing partner requests and users.",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routers
app.include_router(users.router)
app.include_router(partner_requests.router)

# Global Exception Handler for RequestValidationError (Pydantic validation errors)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify that the API is running.
    """
    return {"status": "ok"} 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)

