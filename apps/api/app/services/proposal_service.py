import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from apps.api.app.models.entities import (
    PolicyProposalRecord,
    Project,
    TopologySnapshot,
)
from apps.api.app.schemas.contracts import (
    ConfigDiffResponse,
    PolicyRequirement,
    ProposalCreateRequest,
    ProposalResponse,
    SimulationRequest,
    SimulationResponse,
    TopologyGraph,
)
from apps.api.app.core.config import settings
from apps.api.app.services.project_service import ProjectService
from engine.policy_engine.gemma_adapter import GemmaAdapter
from engine.policy_engine.synthesizer import PolicySynthesizer


class ProposalService:
    @staticmethod
    def create_proposal(
        db: Session, project_id: str, request: ProposalCreateRequest
    ) -> ProposalResponse:
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        baseline_topology = ProjectService.get_topology(db, project_id, "baseline")
        if not baseline_topology:
            raise HTTPException(status_code=404, detail="Baseline topology not found")

        # 1. Generate structured proposal via Gemma 4 Adapter (or use explicit override)
        if request.requirements_override is not None:
            requirements = request.requirements_override
            reason = "User-edited policy requirements"
            meta = {
                "thinking_trace": ["Manual override applied by developer."],
                "risk_assessment": "Custom developer policy rules.",
                "model_used": settings.GEMMA_MODEL_NAME,
                "provider_used": "manual_override",
                "latency_ms": 0,
                "raw_output": "",
            }
        else:
            gemma_res = GemmaAdapter.generate_proposal(
                request.intent, baseline_topology, source_yaml=project.source_yaml
            )
            gemma_out = gemma_res["proposal"]
            requirements = gemma_out.requirements
            reason = gemma_out.reason
            meta = {
                "thinking_trace": gemma_out.thinking_trace,
                "risk_assessment": gemma_out.risk_assessment,
                "model_used": gemma_res["model_used"],
                "provider_used": gemma_res["provider_used"],
                "latency_ms": gemma_res["latency_ms"],
                "raw_output": gemma_res["raw_output"],
            }

        # 2. Run semantic validation against baseline topology
        validation_errors = PolicySynthesizer.validate_requirements(
            requirements, baseline_topology
        )
        status_str = "validated" if not validation_errors else "rejected"

        proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
        record = PolicyProposalRecord(
            id=proposal_id,
            project_id=project_id,
            intent=request.intent,
            requirements_json=[r.model_dump() for r in requirements],
            reason=reason,
            status=status_str,
            validation_errors_json=validation_errors,
            simulation_json={"gemma_meta": meta},
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return ProposalService._to_response(record)

    @staticmethod
    def validate_proposal(
        db: Session,
        project_id: str,
        proposal_id: str,
        requirements_override: list[PolicyRequirement] | None = None,
    ) -> ProposalResponse:
        record = (
            db.query(PolicyProposalRecord)
            .filter(
                PolicyProposalRecord.id == proposal_id,
                PolicyProposalRecord.project_id == project_id,
            )
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Proposal not found")

        baseline_topology = ProjectService.get_topology(db, project_id, "baseline")
        if not baseline_topology:
            raise HTTPException(status_code=404, detail="Baseline topology not found")

        if requirements_override is not None:
            requirements = requirements_override
            record.requirements_json = [r.model_dump() for r in requirements]
        else:
            requirements = [PolicyRequirement.model_validate(r) for r in record.requirements_json]

        errors = PolicySynthesizer.validate_requirements(requirements, baseline_topology)
        record.validation_errors_json = errors
        record.status = "validated" if not errors else "rejected"

        db.commit()
        db.refresh(record)
        return ProposalService._to_response(record)

    @staticmethod
    def run_simulation(
        db: Session, project_id: str, request: SimulationRequest
    ) -> SimulationResponse:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        record = (
            db.query(PolicyProposalRecord)
            .filter(
                PolicyProposalRecord.id == request.proposal_id,
                PolicyProposalRecord.project_id == project_id,
            )
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Proposal not found")

        baseline_topology = ProjectService.get_topology(db, project_id, "baseline")
        if not baseline_topology:
            raise HTTPException(status_code=404, detail="Baseline topology not found")

        # Allow user edits from the UI requirements editor before simulating
        if request.requirements_override is not None:
            requirements = request.requirements_override
            record.requirements_json = [r.model_dump() for r in requirements]
        else:
            requirements = [PolicyRequirement.model_validate(r) for r in record.requirements_json]

        # Ensure proposal passes validation before simulating
        errors = PolicySynthesizer.validate_requirements(requirements, baseline_topology)
        if errors:
            record.validation_errors_json = errors
            record.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Cannot simulate invalid proposal: {'; '.join(errors)}",
            )

        sim_result = PolicySynthesizer.simulate(
            project_id=project_id,
            proposal_id=record.id,
            baseline_yaml=project.source_yaml,
            baseline_topology=baseline_topology,
            requirements=requirements,
        )

        sim_id = f"sim_{uuid.uuid4().hex[:8]}"
        candidate_topology: TopologyGraph = sim_result["candidate_topology"]

        # Persist candidate snapshot (without mutating baseline)
        version_tag = f"candidate:{record.id}"
        existing_snap = (
            db.query(TopologySnapshot)
            .filter(
                TopologySnapshot.project_id == project_id,
                TopologySnapshot.version == version_tag,
            )
            .first()
        )
        if existing_snap:
            existing_snap.graph_json = candidate_topology.model_dump()
            existing_snap.compose_yaml = sim_result["candidate_yaml"]
        else:
            db.add(
                TopologySnapshot(
                    id=f"snap_{uuid.uuid4().hex[:8]}",
                    project_id=project_id,
                    version=version_tag,
                    graph_json=candidate_topology.model_dump(),
                    compose_yaml=sim_result["candidate_yaml"],
                )
            )

        response_obj = SimulationResponse(
            simulation_id=sim_id,
            project_id=project_id,
            proposal_id=record.id,
            baseline_reachability=sim_result["baseline_reachability"],
            candidate_reachability=sim_result["candidate_reachability"],
            impacts=sim_result["impacts"],
            candidate_topology=candidate_topology,
            candidate_yaml=sim_result["candidate_yaml"],
            yaml_diff=sim_result["yaml_diff"],
            execution_performed=False,
        )

        record.status = "simulated"
        record.candidate_yaml = sim_result["candidate_yaml"]
        existing_meta = (record.simulation_json or {}).get("gemma_meta", {})
        sim_dump = response_obj.model_dump(mode="json")
        sim_dump["gemma_meta"] = existing_meta
        record.simulation_json = sim_dump
        db.commit()

        return response_obj

    @staticmethod
    def get_diff(
        db: Session, project_id: str, proposal_id: str | None = None
    ) -> ConfigDiffResponse:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        query = db.query(PolicyProposalRecord).filter(
            PolicyProposalRecord.project_id == project_id,
            PolicyProposalRecord.candidate_yaml.isnot(None),
        )
        if proposal_id:
            query = query.filter(PolicyProposalRecord.id == proposal_id)
        record = query.order_by(PolicyProposalRecord.created_at.desc()).first()

        if not record or not record.candidate_yaml:
            raise HTTPException(
                status_code=404,
                detail="No simulated candidate configuration found for this project.",
            )

        yaml_diff = ""
        if record.simulation_json and "yaml_diff" in record.simulation_json:
            yaml_diff = record.simulation_json["yaml_diff"]

        return ConfigDiffResponse(
            project_id=project_id,
            proposal_id=record.id,
            baseline_yaml=project.source_yaml,
            candidate_yaml=record.candidate_yaml,
            yaml_diff=yaml_diff,
        )

    @staticmethod
    def list_proposals(db: Session, project_id: str) -> list[ProposalResponse]:
        records = (
            db.query(PolicyProposalRecord)
            .filter(PolicyProposalRecord.project_id == project_id)
            .order_by(PolicyProposalRecord.created_at.desc())
            .all()
        )
        return [ProposalService._to_response(r) for r in records]

    @staticmethod
    def _to_response(record: PolicyProposalRecord) -> ProposalResponse:
        meta = (record.simulation_json or {}).get("gemma_meta", {})
        return ProposalResponse(
            id=record.id,
            project_id=record.project_id,
            intent=record.intent,
            requirements=[PolicyRequirement(**r) for r in (record.requirements_json or [])],
            reason=record.reason or "",
            thinking_trace=meta.get("thinking_trace", []),
            risk_assessment=meta.get("risk_assessment", ""),
            model_used=meta.get("model_used", settings.GEMMA_MODEL_NAME),
            provider_used=meta.get("provider_used", settings.GEMMA_PROVIDER),
            latency_ms=meta.get("latency_ms", 0),
            raw_output=meta.get("raw_output", ""),
            status=record.status,
            validation_errors=record.validation_errors_json or [],
            created_at=record.created_at,
        )