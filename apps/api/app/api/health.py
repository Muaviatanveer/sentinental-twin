import docker
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.schemas.contracts import HealthStatusResponse

router = APIRouter()


@router.get("/health", response_model=HealthStatusResponse)
def check_health(db: Session = Depends(get_db)) -> HealthStatusResponse:
    # 1. Check SQLite Database
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # 2. Check Docker Engine availability
    docker_ok = False
    docker_detail = "Docker daemon unreachable"
    try:
        client = docker.from_env(timeout=2)
        if client.ping():
            docker_ok = True
            docker_detail = "Docker Engine connected"
    except Exception as exc:
        docker_detail = f"Docker unavailable ({exc.__class__.__name__})"

    return HealthStatusResponse(
        status="ok" if db_ok else "degraded",
        version=settings.VERSION,
        database_connected=db_ok,
        docker_available=docker_ok,
        docker_detail=docker_detail,
        gemma_provider=settings.GEMMA_PROVIDER,
        gemma_model=settings.GEMMA_MODEL_NAME,
        gemma_ready=True,
        sandbox_enabled=settings.DOCKER_SANDBOX_ENABLED,
    )


from apps.api.app.schemas.contracts import GemmaConfigUpdateRequest


@router.post("/settings/gemma", response_model=HealthStatusResponse)
def update_gemma_settings(
    req: GemmaConfigUpdateRequest, db: Session = Depends(get_db)
) -> HealthStatusResponse:
    settings.GEMMA_PROVIDER = req.provider
    settings.GEMMA_MODEL_NAME = req.model_name
    if req.api_key is not None:
        settings.GEMMA_API_KEY = req.api_key.strip()
    if req.api_base is not None:
        settings.GEMMA_API_BASE = req.api_base.strip()
    return check_health(db)