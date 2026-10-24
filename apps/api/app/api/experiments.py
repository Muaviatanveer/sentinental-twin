from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from apps.api.app.core.database import get_db
from apps.api.app.schemas.contracts import (
    DashboardMetricsResponse,
    ExperimentCreateRequest,
    ExperimentResponse,
    VerificationReportResponse,
)
from apps.api.app.services.experiment_service import ExperimentService
from apps.api.app.services.report_service import ReportService

router = APIRouter()


@router.post(
    "/projects/{project_id}/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_experiment(
    project_id: str,
    request: ExperimentCreateRequest,
    db: Session = Depends(get_db),
):
    return ExperimentService.create_experiment(
        db, project_id, request.proposal_id
    )


@router.post(
    "/experiments/{experiment_id}/run",
    response_model=ExperimentResponse,
)
def run_experiment(experiment_id: str, db: Session = Depends(get_db)):
    return ExperimentService.run_experiment(db, experiment_id)


@router.get(
    "/experiments/{experiment_id}",
    response_model=ExperimentResponse,
)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    return ExperimentService.get_experiment(db, experiment_id)


@router.get(
    "/experiments/{experiment_id}/report",
    response_model=VerificationReportResponse,
)
def get_experiment_report(experiment_id: str, db: Session = Depends(get_db)):
    return ReportService.generate_or_get_report(db, experiment_id)


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    return ReportService.get_dashboard_metrics(db)
