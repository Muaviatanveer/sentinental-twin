from datetime import datetime, timezone
import uuid
import yaml
from fastapi import HTTPException
from sqlalchemy.orm import Session
from apps.api.app.models.entities import (
    EvidenceItemRecord,
    ExperimentRecord,
    PolicyProposalRecord,
    TestCaseRecord,
)
from apps.api.app.schemas.contracts import (
    EvidenceRecordSchema,
    ExperimentResponse,
    PolicyRequirement,
    TestCaseSchema,
)
from apps.api.app.services.project_service import ProjectService
from engine.experiment_planner.planner import ExperimentPlanner
from engine.sandbox_runner.runner import SandboxRunner
from engine.evidence.collector import EvidenceCollector


class ExperimentService:
    @staticmethod
    def create_experiment(
        db: Session, project_id: str, proposal_id: str
    ) -> ExperimentResponse:
        proposal = (
            db.query(PolicyProposalRecord)
            .filter(
                PolicyProposalRecord.id == proposal_id,
                PolicyProposalRecord.project_id == project_id,
            )
            .first()
        )
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        if not proposal.candidate_yaml:
            raise HTTPException(
                status_code=400,
                detail="Run counterfactual simulation on this proposal before creating an experiment.",
            )

        candidate_topology = ProjectService.get_topology(
            db, project_id, version=f"candidate:{proposal_id}"
        )
        if not candidate_topology:
            raise HTTPException(status_code=404, detail="Candidate topology not found")

        requirements = [
            PolicyRequirement(**r) for r in (proposal.requirements_json or [])
        ]
        raw_candidate_dict = yaml.safe_load(proposal.candidate_yaml)
        plan = ExperimentPlanner.build_test_plan(
            requirements, candidate_topology, raw_candidate_dict
        )

        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        exp_record = ExperimentRecord(
            id=exp_id,
            project_id=project_id,
            proposal_id=proposal_id,
            status="ready",
        )
        db.add(exp_record)

        for item in plan:
            db.add(
                TestCaseRecord(
                    id=f"tc_{uuid.uuid4().hex[:8]}",
                    experiment_id=exp_id,
                    source=item["source"],
                    destination=item["destination"],
                    target_port=item["target_port"],
                    expected=item["expected"],
                    predicted=item["predicted"],
                    observed="not_run",
                )
            )

        db.commit()
        return ExperimentService.get_experiment(db, exp_id)

    @staticmethod
    def run_experiment(db: Session, experiment_id: str) -> ExperimentResponse:
        exp = (
            db.query(ExperimentRecord)
            .filter(ExperimentRecord.id == experiment_id)
            .first()
        )
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        proposal = (
            db.query(PolicyProposalRecord)
            .filter(PolicyProposalRecord.id == exp.proposal_id)
            .first()
        )
        if not proposal or not proposal.candidate_yaml:
            raise HTTPException(
                status_code=400, detail="Candidate YAML missing for experiment"
            )

        test_records = (
            db.query(TestCaseRecord)
            .filter(TestCaseRecord.experiment_id == experiment_id)
            .all()
        )
        plan = [
            {
                "source": tc.source,
                "destination": tc.destination,
                "target_port": tc.target_port,
                "expected": tc.expected,
                "predicted": tc.predicted,
            }
            for tc in test_records
        ]

        exp.status = "running"
        db.commit()

        try:
            outcome = SandboxRunner.execute_test_plan(
                experiment_id=experiment_id,
                candidate_yaml=proposal.candidate_yaml,
                test_plan=plan,
            )

            # Update TestCaseRecords with real runtime observations
            for tc_rec, res in zip(test_records, outcome["results"]):
                tc_rec.observed = res["observed"]
                tc_rec.actual_outcome = res["actual_outcome"]
                tc_rec.discrepancy = res["discrepancy"]
                tc_rec.exit_code = res["exit_code"]
                tc_rec.output_log = res["output_log"]
                tc_rec.timestamp = datetime.now(timezone.utc)

            # Store Cryptographic Evidence Records
            runner_log = outcome["runner_log"]
            db.add(
                EvidenceItemRecord(
                    id=f"ev_{uuid.uuid4().hex[:8]}",
                    experiment_id=experiment_id,
                    kind="sandbox_execution_log",
                    content=runner_log,
                    content_hash=EvidenceCollector.hash_content(runner_log),
                )
            )
            sanitized_yaml = outcome["sanitized_yaml"]
            db.add(
                EvidenceItemRecord(
                    id=f"ev_{uuid.uuid4().hex[:8]}",
                    experiment_id=experiment_id,
                    kind="sanitized_sandbox_compose",
                    content=sanitized_yaml,
                    content_hash=EvidenceCollector.hash_content(sanitized_yaml),
                )
            )

            exp.status = "completed"
            exp.duration_ms = outcome["duration_ms"]
            exp.finished_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as exc:
            exp.status = "failed"
            exp.finished_at = datetime.now(timezone.utc)
            err_text = f"Sandbox execution error: {str(exc)}"
            db.add(
                EvidenceItemRecord(
                    id=f"ev_{uuid.uuid4().hex[:8]}",
                    experiment_id=experiment_id,
                    kind="execution_error",
                    content=err_text,
                    content_hash=EvidenceCollector.hash_content(err_text),
                )
            )
            db.commit()
            raise HTTPException(status_code=500, detail=err_text)

        return ExperimentService.get_experiment(db, experiment_id)

    @staticmethod
    def get_experiment(db: Session, experiment_id: str) -> ExperimentResponse:
        exp = (
            db.query(ExperimentRecord)
            .filter(ExperimentRecord.id == experiment_id)
            .first()
        )
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        tcs = (
            db.query(TestCaseRecord)
            .filter(TestCaseRecord.experiment_id == experiment_id)
            .all()
        )
        evs = (
            db.query(EvidenceItemRecord)
            .filter(EvidenceItemRecord.experiment_id == experiment_id)
            .order_by(EvidenceItemRecord.timestamp.asc())
            .all()
        )

        return ExperimentResponse(
            id=exp.id,
            project_id=exp.project_id,
            proposal_id=exp.proposal_id,
            status=exp.status,
            created_at=exp.created_at,
            finished_at=exp.finished_at,
            duration_ms=exp.duration_ms,
            test_cases=[
                TestCaseSchema(
                    id=t.id,
                    source=t.source,
                    destination=t.destination,
                    target_port=t.target_port,
                    expected=t.expected,
                    predicted=t.predicted,
                    observed=t.observed,
                    actual_outcome=t.actual_outcome,
                    discrepancy=t.discrepancy,
                    exit_code=t.exit_code,
                    output_log=t.output_log,
                    timestamp=t.timestamp,
                )
                for t in tcs
            ],
            evidence=[
                EvidenceRecordSchema(
                    id=e.id,
                    kind=e.kind,
                    content=e.content,
                    content_hash=e.content_hash,
                    timestamp=e.timestamp,
                )
                for e in evs
            ],
        )
