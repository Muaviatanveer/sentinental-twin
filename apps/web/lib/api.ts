import { HealthStatusResponse } from "./types";

export const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchHealthStatus(): Promise<HealthStatusResponse> {
    const res = await fetch(`${API_BASE_URL}/health`, {
        cache: "no-store",
    });
    if (!res.ok) {
        throw new Error(`Health check failed with status ${res.status}`);
    }
    return res.json();
}
import { TopologyGraph } from "./types";

export async function createSampleProject(): Promise<{ id: string }> {
    const res = await fetch(`${API_BASE_URL}/projects/sample`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error("Failed to load sample project");
    return res.json();
}

export async function uploadProject(name: string, yamlContent: string): Promise<{ id: string }> {
    const res = await fetch(`${API_BASE_URL}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, yaml_content: yamlContent }),
    });
    if (!res.ok) throw new Error("Failed to upload project");
    return res.json();
}

export async function getProjectTopology(id: string): Promise<TopologyGraph> {
    const res = await fetch(`${API_BASE_URL}/projects/${id}/topology`, {
        cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch topology");
    return res.json();
}
import {
    PolicyRequirement,
    ProposalResponse,
    SimulationResponse,
    ExperimentResponse,
    DashboardMetricsResponse,
    VerificationReportResponse,
} from "./types";

export async function generateProposal(
    projectId: string,
    intent: string,
    requirementsOverride?: PolicyRequirement[]
): Promise<ProposalResponse> {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/proposals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            intent,
            mode: "propose_only",
            requirements_override: requirementsOverride,
        }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to generate proposal");
    }
    return res.json();
}

export async function validateProposal(
    projectId: string,
    proposalId: string,
    requirements: PolicyRequirement[]
): Promise<ProposalResponse> {
    const res = await fetch(
        `${API_BASE_URL}/projects/${projectId}/proposals/${proposalId}/validate`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ requirements }),
        }
    );
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to validate proposal");
    }
    return res.json();
}

export async function simulateProposal(
    projectId: string,
    proposalId: string,
    requirementsOverride?: PolicyRequirement[]
): Promise<SimulationResponse> {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/simulations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            proposal_id: proposalId,
            requirements_override: requirementsOverride,
        }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Simulation failed");
    }
    return res.json();
}

export async function createExperiment(
  projectId: string,
  proposalId: string
): Promise<ExperimentResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/experiments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ proposal_id: proposalId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create experiment");
  }
  return res.json();
}

export async function runExperiment(
  experimentId: string
): Promise<ExperimentResponse> {
  const res = await fetch(`${API_BASE_URL}/experiments/${experimentId}/run`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Sandbox execution failed");
  }
  return res.json();
}

export async function getExperiment(
  experimentId: string
): Promise<ExperimentResponse> {
  const res = await fetch(`${API_BASE_URL}/experiments/${experimentId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch experiment");
  }
  return res.json();
}

export async function getExperimentReport(
  experimentId: string
): Promise<VerificationReportResponse> {
  const res = await fetch(`${API_BASE_URL}/experiments/${experimentId}/report`, {
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load verification report");
  }
  return res.json();
}

export async function fetchDashboardMetrics(): Promise<DashboardMetricsResponse> {
  const res = await fetch(`${API_BASE_URL}/metrics`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load metrics");
  return res.json();
}

export async function updateGemmaConfig(payload: {
  provider: string;
  model_name: string;
  api_key?: string;
  api_base?: string;
}): Promise<HealthStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/settings/gemma`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to update Gemma 4 configuration");
  return res.json();
}