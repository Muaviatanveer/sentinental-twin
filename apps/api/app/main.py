from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.core.config import settings
from apps.api.app.core.database import Base, engine
from apps.api.app.models import entities  # noqa: F401
from apps.api.app.api.health import router as health_router
from apps.api.app.api.projects import router as projects_router
from apps.api.app.api.experiments import router as experiments_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Initialize SQLite tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_V1_STR, tags=["diagnostics"])
app.include_router(projects_router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(experiments_router, prefix=settings.API_V1_STR, tags=["experiments"])

@app.get("/")
def root():
    return {
        "product": settings.PROJECT_NAME,
        "tagline": "Test Tomorrow's Infrastructure Decisions Today.",
        "docs": "/docs",
    }