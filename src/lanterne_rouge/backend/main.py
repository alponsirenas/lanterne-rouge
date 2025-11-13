"""FastAPI application main module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lanterne_rouge.backend.api import auth, health, missions
from lanterne_rouge.backend.core.config import get_settings

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(missions.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Lanterne Rouge API",
        "version": settings.api_version,
        "docs": "/docs"
    }
