"""FastAPI application main module."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lanterne_rouge.backend.api import auth, connections, health, jobs, missions
from lanterne_rouge.backend.core.config import get_settings
from lanterne_rouge.backend.services.mission_scheduler import MissionTransitionScheduler
from lanterne_rouge.backend.services.background_refresh import get_refresh_scheduler

settings = get_settings()

# Mission transition scheduler
mission_scheduler = MissionTransitionScheduler(
    interval_minutes=settings.mission_transition_check_interval_minutes
)

# Background refresh scheduler for data connections
refresh_scheduler = get_refresh_scheduler(interval_minutes=60)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage application lifespan events."""
    # Startup
    if settings.enable_mission_scheduler:
        await mission_scheduler.start()
    
    # Always start background refresh for data connections
    await refresh_scheduler.start()

    yield

    # Shutdown
    if settings.enable_mission_scheduler:
        await mission_scheduler.stop()
    
    await refresh_scheduler.stop()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
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
app.include_router(jobs.router)
app.include_router(connections.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Lanterne Rouge API",
        "version": settings.api_version,
        "docs": "/docs"
    }
