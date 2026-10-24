from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from apps.api.app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    source_yaml = Column(Text, nullable=False)
    source_hash = Column(String, nullable=False)
    warnings_json = Column(JSON, default=list)


class ServiceRecord(Base):
    __tablename__ = "services"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=True)
    ports_json = Column(JSON, default=list)
    networks_json = Column(JSON, default=list)
    depends_on_json = Column(JSON, default=list)
    security_settings_json = Column(JSON, default=dict)


class NetworkRecord(Base):
    __tablename__ = "networks"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    internal = Column(Boolean, default=False)
    driver = Column(String, default="bridge")


class TopologySnapshot(Base):
    __tablename__ = "topology_snapshots"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    version = Column(String, nullable=False)  # "baseline" or "candidate:<proposal_id>"
    graph_json = Column(JSON, nullable=False)
    compose_yaml = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class PolicyProposalRecord(Base):
    __tablename__ = "policy_proposals"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    intent = Column(Text, nullable=False)
    requirements_json = Column(JSON, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft | validated | rejected | simulated
    validation_errors_json = Column(JSON, default=list)
    simulation_json = Column(JSON, nullable=True)
    candidate_yaml = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class ExperimentRecord(Base):
    __tablename__ = "experiments"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    proposal_id = Column(String, ForeignKey("policy_proposals.id", ondelete="CASCADE"), index=True)
    status = Column(String, default="ready")  # ready | queued | running | completed | failed | timed_out
    created_at = Column(DateTime, default=utc_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)


class TestCaseRecord(Base):
    __tablename__ = "test_cases"

    id = Column(String, primary_key=True, index=True)
    experiment_id = Column(String, ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    target_port = Column(Integer, nullable=False)
    expected = Column(String, nullable=False)  # allow | deny
    predicted = Column(String, nullable=False)  # allow | deny
    observed = Column(String, default="not_run")  # pass | fail | inconclusive | not_run
    actual_outcome = Column(String, nullable=True)  # reachable | blocked | error
    discrepancy = Column(Boolean, default=False)
    exit_code = Column(Integer, nullable=True)
    output_log = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now)


class EvidenceItemRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(String, primary_key=True, index=True)
    experiment_id = Column(String, ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    kind = Column(String, nullable=False)  # probe_log | compose_diff | runtime_summary
    content = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)


class ReportRecord(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    experiment_id = Column(String, ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    summary_json = Column(JSON, nullable=False)
    markdown_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)