from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from apps.api.app.core.database import get_db
from apps.api.app.core.config import ROOT_DIR
from apps.api.app.schemas.contracts import (
    ConfigDiffResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProposalCreateRequest,
    ProposalResponse,
    ProposalValidateRequest,
    SimulationRequest,
    SimulationResponse,
    TopologyGraph,
)
from apps.api.app.services.project_service import ProjectService
from apps.api.app.services.proposal_service import ProposalService

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(request: ProjectCreateRequest, db: Session = Depends(get_db)):
    try:
        project = ProjectService.create_project(db, request.name, request.yaml_content)
        return ProjectResponse(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            source_hash=project.source_hash,
            warnings=project.warnings_json,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sample", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def load_sample_project(db: Session = Depends(get_db)):
    """Convenience endpoint to load the hackathon default fixture."""
    fixture_path = ROOT_DIR / "fixtures" / "commerce-app" / "compose.yaml"
    if not fixture_path.exists():
        raise HTTPException(status_code=404, detail="Sample fixture not found on disk.")

    yaml_content = fixture_path.read_text(encoding="utf-8")

    try:
        project = ProjectService.create_project(db, "Sample Commerce App", yaml_content)
        return ProjectResponse(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            source_hash=project.source_hash,
            warnings=project.warnings_json,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        source_hash=project.source_hash,
        warnings=project.warnings_json,
    )


@router.get("/{project_id}/topology", response_model=TopologyGraph)
def get_project_topology(
    project_id: str,
    version: str = Query(default="baseline"),
    db: Session = Depends(get_db),
):
    topology = ProjectService.get_topology(db, project_id, version=version)
    if not topology:
        raise HTTPException(status_code=404, detail="Topology not found")
    return topology


@router.post(
    "/{project_id}/proposals",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_proposal(
    project_id: str,
    request: ProposalCreateRequest,
    db: Session = Depends(get_db),
):
    return ProposalService.create_proposal(db, project_id, request)


@router.get("/{project_id}/proposals", response_model=list[ProposalResponse])
def list_proposals(project_id: str, db: Session = Depends(get_db)):
    return ProposalService.list_proposals(db, project_id)


@router.post(
    "/{project_id}/proposals/{proposal_id}/validate",
    response_model=ProposalResponse,
)
def validate_proposal(
    project_id: str,
    proposal_id: str,
    request: ProposalValidateRequest,
    db: Session = Depends(get_db),
):
    return ProposalService.validate_proposal(
        db, project_id, proposal_id, request.requirements
    )


@router.post("/{project_id}/simulations", response_model=SimulationResponse)
def simulate_proposal(
    project_id: str,
    request: SimulationRequest,
    db: Session = Depends(get_db),
):
    return ProposalService.run_simulation(db, project_id, request)


@router.get("/{project_id}/diff", response_model=ConfigDiffResponse)
def get_project_diff(
    project_id: str,
    proposal_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return ProposalService.get_diff(db, project_id, proposal_id=proposal_id)