import difflib
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from apps.api.app.models.entities import (
    ExperimentRecord,
    PolicyProposalRecord,
    Project,
    ReportRecord,
    TestCaseRecord,
    TopologySnapshot,
)
from apps.api.app.schemas.contracts import (
    DashboardMetricsResponse,
    VerificationReportResponse,
)
from apps.api.app.services.experiment_service import ExperimentService
from engine.evidence.collector import EvidenceCollector


class ReportService:
    @staticmethod
    def generate_or_get_report(
        db: Session, experiment_id: str
    ) -> VerificationReportResponse:
        exp_resp = ExperimentService.get_experiment(db, experiment_id)
        project = (
            db.query(Project).filter(Project.id == exp_resp.project_id).first()
        )
        proposal = (
            db.query(PolicyProposalRecord)
            .filter(PolicyProposalRecord.id == exp_resp.proposal_id)
            .first()
        )
        if not project or not proposal:
            raise HTTPException(
                status_code=404, detail="Project or proposal not found"
            )

        candidate_yaml = proposal.candidate_yaml or project.source_yaml
        baseline_hash = project.source_hash
        candidate_hash = EvidenceCollector.hash_content(candidate_yaml)

        yaml_diff = "\n".join(
            difflib.unified_diff(
                project.source_yaml.splitlines(),
                candidate_yaml.splitlines(),
                fromfile="compose.baseline.yaml",
                tofile="compose.candidate.yaml",
                lineterm="",
            )
        )

        total_reqs = len(exp_resp.test_cases)
        verified_passed = sum(
            1 for t in exp_resp.test_cases if t.observed == "pass"
        )
        regressions = sum(
            1
            for t in exp_resp.test_cases
            if t.expected == "allow" and t.observed == "fail"
        )
        discrepancies = sum(1 for t in exp_resp.test_cases if t.discrepancy)

        limitations = [
            "L3/L4 TCP reachability probes verify container network isolation but do not inspect L7 application authentication.",
            "Disposable sandbox strips host volume mounts and host port bindings to protect the host kernel.",
            "Cryptographic SHA-256 hashes establish integrity of recorded test logs, not formal proof of absence of all vulnerabilities.",
        ]

        # Build Markdown report
        md_lines = [
            f"# NeuroSyn Sentinel Twin — Verification Report (`{experiment_id}`)",
            "",
            f"- **Project:** `{project.name}` (`{project.id}`)",
            f"- **Proposal ID:** `{proposal.id}`",
            f"- **Security Intent:** {proposal.intent}",
            f"- **Baseline SHA-256:** `{baseline_hash}`",
            f"- **Candidate SHA-256:** `{candidate_hash}`",
            f"- **Execution Duration:** `{exp_resp.duration_ms or 0} ms`",
            "",
            "## 1. Summary Metrics",
            f"- **Requirements Evaluated:** {total_reqs}",
            f"- **Requirements Verified (Pass):** {verified_passed}/{total_reqs}",
            f"- **Regressions Detected:** {regressions}",
            f"- **Model Discrepancies (Prediction vs. Runtime):** {discrepancies}",
            "",
            "## 2. Connectivity Probe Matrix",
            "| Source → Destination | Expected | Predicted | Observed Runtime | Exit Code | Grade |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for tc in exp_resp.test_cases:
            md_lines.append(
                f"| `{tc.source} -> {tc.destination}:{tc.target_port}` | `{tc.expected.upper()}` | "
                f"`{tc.predicted.upper()}` | `{tc.actual_outcome or 'N/A'}` | `{tc.exit_code}` | **{tc.observed.upper()}** |"
            )

        md_lines.extend(
            [
                "",
                "## 3. Proposed Compose Configuration Diff",
                "```diff",
                yaml_diff,
                "```",
                "",
                "## 4. Explicit Modeling Assumptions & Limitations",
            ]
        )
        for lim in limitations:
            md_lines.append(f"- {lim}")

        markdown_text = "\n".join(md_lines)

        existing_rep = (
            db.query(ReportRecord)
            .filter(ReportRecord.experiment_id == experiment_id)
            .first()
        )
        report_id = existing_rep.id if existing_rep else f"rep_{uuid.uuid4().hex[:8]}"

        resp = VerificationReportResponse(
            report_id=report_id,
            project_id=project.id,
            experiment_id=experiment_id,
            proposal_id=proposal.id,
            intent=proposal.intent,
            baseline_hash=baseline_hash,
            candidate_hash=candidate_hash,
            status=exp_resp.status,
            duration_ms=exp_resp.duration_ms,
            total_requirements=total_reqs,
            verified_passed=verified_passed,
            regressions_detected=regressions,
            model_discrepancies=discrepancies,
            test_cases=exp_resp.test_cases,
            evidence=exp_resp.evidence,
            baseline_yaml=project.source_yaml,
            candidate_yaml=candidate_yaml,
            yaml_diff=yaml_diff,
            markdown_report=markdown_text,
            limitations=limitations,
            created_at=exp_resp.created_at,
        )

        if not existing_rep:
            db.add(
                ReportRecord(
                    id=report_id,
                    project_id=project.id,
                    experiment_id=experiment_id,
                    summary_json=resp.model_dump(mode="json"),
                    markdown_content=markdown_text,
                )
            )
            db.commit()

        return resp

    @staticmethod
    def get_dashboard_metrics(db: Session) -> DashboardMetricsResponse:
        projects = db.query(Project).all()
        snapshots = (
            db.query(TopologySnapshot)
            .filter(TopologySnapshot.version == "baseline")
            .all()
        )
        services_count = sum(
            len(s.graph_json.get("services", [])) for s in snapshots
        )
        networks_count = sum(
            len(s.graph_json.get("networks", [])) for s in snapshots
        )

        all_tcs = db.query(TestCaseRecord).all()
        verified = sum(1 for t in all_tcs if t.observed == "pass")
        regressions = sum(
            1 for t in all_tcs if t.expected == "allow" and t.observed == "fail"
        )
        discrepancies = sum(1 for t in all_tcs if t.discrepancy)

        last_exp = (
            db.query(ExperimentRecord)
            .filter(ExperimentRecord.duration_ms.isnot(None))
            .order_by(ExperimentRecord.created_at.desc())
            .first()
        )

        return DashboardMetricsResponse(
            projects_count=len(projects),
            services_modeled=services_count,
            networks_modeled=networks_count,
            requirements_evaluated=len(all_tcs),
            requirements_verified=verified,
            regressions_detected=regressions,
            model_discrepancies=discrepancies,
            last_execution_duration_ms=last_exp.duration_ms if last_exp else None,
        )
