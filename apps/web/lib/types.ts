export type RelationshipType =
    | "shares_network"
    | "depends_on"
    | "publishes_port"
    | "declared_access"
    | "observed_connectivity";

export type ExpectedAction = "allow" | "deny";
export type ObservedGrade = "pass" | "fail" | "inconclusive" | "not_run";

export interface PortMapping {
    host_port?: number | null;
    container_port: number;
    protocol: string;
    published: boolean;
}

export interface ServiceNode {
    id: string;
    name: string;
    image?: string | null;
    networks: string[];
    published_ports: PortMapping[];
    depends_on: string[];
    security_settings: Record<string, unknown>;
}

export interface NetworkNode {
    id: string;
    name: string;
    internal: boolean;
    driver: string;
}

export interface RelationshipEdge {
    id: string;
    source: string;
    target: string;
    relationship: RelationshipType;
    label: string;
    metadata: Record<string, unknown>;
    diff_status: "unchanged" | "newly_blocked" | "newly_permitted" | "unverified";
}

export interface TopologyGraph {
    project_id: string;
    version: string;
    services: ServiceNode[];
    networks: NetworkNode[];
    edges: RelationshipEdge[];
    reachability_matrix: Record<string, Record<string, string>>;
    warnings: string[];
}

export interface HealthStatusResponse {
    status: "ok" | "degraded";
    version: string;
    database_connected: boolean;
    docker_available: boolean;
    docker_detail: string;
    gemma_provider: string;
    gemma_model: string;
    gemma_ready: boolean;
    sandbox_enabled: boolean;
}

export interface PolicyRequirement {
    source: string;
    destination: string;
    expected: ExpectedAction;
}

export interface ProposalResponse {
  id: string;
  project_id: string;
  intent: string;
  requirements: PolicyRequirement[];
  reason: string;
  thinking_trace?: string[];
  risk_assessment?: string;
  model_used?: string;
  provider_used?: string;
  latency_ms?: number;
  raw_output?: string;
  status: "draft" | "validated" | "rejected" | "simulated";
  validation_errors: string[];
  created_at: string;
}

export interface PathImpact {
    source: string;
    destination: string;
    baseline_state: string;
    candidate_state: string;
    change_type: "newly_blocked" | "newly_permitted" | "unchanged" | "conflicting";
    rule_applied: string;
    assumptions: string[];
}

export interface SimulationResponse {
    simulation_id: string;
    project_id: string;
    proposal_id: string;
    baseline_reachability: Record<string, string>;
    candidate_reachability: Record<string, string>;
    impacts: PathImpact[];
    candidate_topology: TopologyGraph;
    candidate_yaml: string;
    yaml_diff: string;
    execution_performed: boolean;
}

export interface TestCaseSchema {
  id: string;
  source: string;
  destination: string;
  target_port: number;
  expected: ExpectedAction;
  predicted: ExpectedAction;
  observed: ObservedGrade;
  actual_outcome?: string | null;
  discrepancy: boolean;
  exit_code?: number | null;
  output_log?: string | null;
  timestamp: string;
}

export interface EvidenceRecordSchema {
  id: string;
  kind: string;
  content: string;
  content_hash: string;
  timestamp: string;
}

export interface ExperimentResponse {
  id: string;
  project_id: string;
  proposal_id: string;
  status: string;
  created_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  test_cases: TestCaseSchema[];
  evidence: EvidenceRecordSchema[];
}

export interface VerificationReportResponse {
  report_id: string;
  project_id: string;
  experiment_id: string;
  proposal_id: string;
  intent: string;
  baseline_hash: string;
  candidate_hash: string;
  status: string;
  duration_ms?: number | null;
  total_requirements: number;
  verified_passed: number;
  regressions_detected: number;
  model_discrepancies: number;
  test_cases: TestCaseSchema[];
  evidence: EvidenceRecordSchema[];
  baseline_yaml: string;
  candidate_yaml: string;
  yaml_diff: string;
  markdown_report: string;
  limitations: string[];
  created_at: string;
}

export interface DashboardMetricsResponse {
  projects_count: number;
  services_modeled: number;
  networks_modeled: number;
  requirements_evaluated: number;
  requirements_verified: number;
  regressions_detected: number;
  model_discrepancies: number;
  last_execution_duration_ms?: number | null;
}