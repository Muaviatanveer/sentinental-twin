from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

RelationshipType = Literal[
    "shares_network",
    "depends_on",
    "publishes_port",
    "declared_access",
    "observed_connectivity",
]

ExpectedAction = Literal["allow", "deny"]
ObservedGrade = Literal["pass", "fail", "inconclusive", "not_run"]


class PortMapping(BaseModel):
    host_port: int | None = None
    container_port: int
    protocol: str = "tcp"
    published: bool = False


class ServiceNode(BaseModel):
    id: str
    name: str
    image: str | None = None
    networks: list[str] = Field(default_factory=list)
    published_ports: list[PortMapping] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    security_settings: dict[str, Any] = Field(default_factory=dict)


class NetworkNode(BaseModel):
    id: str
    name: str
    internal: bool = False
    driver: str = "bridge"


class RelationshipEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: RelationshipType
    label: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    diff_status: Literal["unchanged", "newly_blocked", "newly_permitted", "unverified"] = "unchanged"


class TopologyGraph(BaseModel):
    project_id: str
    version: str = "baseline"
    services: list[ServiceNode]
    networks: list[NetworkNode]
    edges: list[RelationshipEdge]
    reachability_matrix: dict[str, dict[str, str]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class PolicyRequirement(BaseModel):
    source: str = Field(..., description="Source service name")
    destination: str = Field(..., description="Destination service name")
    expected: ExpectedAction = Field(..., description="Whether connectivity should be allow or deny")


class GemmaProposalSchema(BaseModel):
    intent: str = "restrict_service_connectivity"
    thinking_trace: list[str] = Field(
        default_factory=list,
        description="Step-by-step reasoning from Gemma 4 Thinking Mode",
    )
    risk_assessment: str = Field(
        default="",
        description="Architectural vulnerability analysis of the baseline topology",
    )
    requirements: list[PolicyRequirement]
    reason: str


class ProposalCreateRequest(BaseModel):
    intent: str
    mode: Literal["propose_only"] = "propose_only"
    requirements_override: list[PolicyRequirement] | None = None


class ProposalResponse(BaseModel):
    id: str
    project_id: str
    intent: str
    requirements: list[PolicyRequirement]
    reason: str
    thinking_trace: list[str] = Field(default_factory=list)
    risk_assessment: str = ""
    model_used: str = "gemma-4-26b-a4b-it"
    provider_used: str = "google_genai"
    latency_ms: int = 0
    raw_output: str = ""
    status: str
    validation_errors: list[str] = Field(default_factory=list)
    created_at: datetime


class PathImpact(BaseModel):
    source: str
    destination: str
    baseline_state: str
    candidate_state: str
    change_type: Literal["newly_blocked", "newly_permitted", "unchanged", "conflicting"]
    rule_applied: str
    assumptions: list[str] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    simulation_id: str
    project_id: str
    proposal_id: str
    baseline_reachability: dict[str, str]
    candidate_reachability: dict[str, str]
    impacts: list[PathImpact]
    candidate_topology: TopologyGraph
    candidate_yaml: str
    yaml_diff: str
    execution_performed: bool = False

class HealthStatusResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    database_connected: bool
    docker_available: bool
    docker_detail: str
    gemma_provider: str
    gemma_model: str
    gemma_ready: bool
    sandbox_enabled: bool

class ProjectCreateRequest(BaseModel):
    name: str
    yaml_content: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    source_hash: str
    warnings: list[str] = Field(default_factory=list)

class ProposalValidateRequest(BaseModel):
    requirements: list[PolicyRequirement] | None = None


class SimulationRequest(BaseModel):
    proposal_id: str
    requirements_override: list[PolicyRequirement] | None = None


class ConfigDiffResponse(BaseModel):
    project_id: str
    proposal_id: str
    baseline_yaml: str
    candidate_yaml: str
    yaml_diff: str


class ExperimentCreateRequest(BaseModel):
    proposal_id: str


class TestCaseSchema(BaseModel):
    id: str
    source: str
    destination: str
    target_port: int
    expected: ExpectedAction
    predicted: ExpectedAction
    observed: ObservedGrade
    actual_outcome: str | None = None
    discrepancy: bool = False
    exit_code: int | None = None
    output_log: str | None = None
    timestamp: datetime


class EvidenceRecordSchema(BaseModel):
    id: str
    kind: str
    content: str
    content_hash: str
    timestamp: datetime


class ExperimentResponse(BaseModel):
    id: str
    project_id: str
    proposal_id: str
    status: str
    created_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    test_cases: list[TestCaseSchema] = Field(default_factory=list)
    evidence: list[EvidenceRecordSchema] = Field(default_factory=list)


class VerificationReportResponse(BaseModel):
    report_id: str
    project_id: str
    experiment_id: str
    proposal_id: str
    intent: str
    baseline_hash: str
    candidate_hash: str
    status: str
    duration_ms: int | None = None
    total_requirements: int
    verified_passed: int
    regressions_detected: int
    model_discrepancies: int
    test_cases: list[TestCaseSchema]
    evidence: list[EvidenceRecordSchema]
    baseline_yaml: str
    candidate_yaml: str
    yaml_diff: str
    markdown_report: str
    limitations: list[str]
    created_at: datetime


class DashboardMetricsResponse(BaseModel):
    projects_count: int
    services_modeled: int
    networks_modeled: int
    requirements_evaluated: int
    requirements_verified: int
    regressions_detected: int
    model_discrepancies: int
    last_execution_duration_ms: int | None = None


class GemmaConfigUpdateRequest(BaseModel):
    provider: Literal["google_genai", "ollama", "openai_compatible", "deterministic_fallback"]
    model_name: str = "gemma-4-26b-a4b-it"
    api_key: str | None = None
    api_base: str | None = None