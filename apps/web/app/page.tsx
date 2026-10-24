"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  fetchHealthStatus,
  fetchDashboardMetrics,
  createSampleProject,
} from "@/lib/api";
import { DashboardMetricsResponse, HealthStatusResponse } from "@/lib/types";
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Upload,
  Sparkles,
  Boxes,
  ShieldAlert,
  Play,
} from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthStatusResponse | null>(null);
  const [metrics, setMetrics] = useState<DashboardMetricsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);

  useEffect(() => {
    fetchHealthStatus()
      .then(setHealth)
      .catch((err) => setError(err.message));
    fetchDashboardMetrics()
      .then(setMetrics)
      .catch(() => null);
  }, []);

  const handleQuickSample = async () => {
    setLoadingSample(true);
    try {
      const proj = await createSampleProject();
      router.push(`/projects/${proj.id}/topology`);
    } catch (err: any) {
      setError(err.message);
      setLoadingSample(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-200 pb-6">
        <div>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-neutral-100 text-neutral-700 border border-neutral-200">
            Counterfactual Infrastructure Testing
          </span>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-neutral-900">
            NeuroSyn Sentinel Twin
          </h1>
          <p className="mt-1 text-sm text-neutral-600 max-w-2xl">
            Import a Docker Compose topology, propose security boundaries in natural language with Gemma 4, simulate graph reachability changes, and verify outcomes in an isolated twin.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleQuickSample}
            disabled={loadingSample}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-medium bg-white border border-neutral-300 text-neutral-800 hover:bg-neutral-50 transition-colors"
          >
            <Play className="h-3.5 w-3.5 text-blue-600" />
            {loadingSample ? "Loading..." : "Open Sample Project"}
          </button>
          <Link
            href="/projects/new"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-medium bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
          >
            <Upload className="h-3.5 w-3.5" />
            Import Compose File
          </Link>
        </div>
      </div>

      {/* Section 17 Live Telemetry Metrics */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          <div className="bg-white border border-neutral-200 rounded-lg p-3.5">
            <div className="text-[10px] uppercase font-semibold text-neutral-400">
              Services Modeled
            </div>
            <div className="text-lg font-semibold text-neutral-900 mt-0.5">
              {metrics.services_modeled}
            </div>
          </div>
          <div className="bg-white border border-neutral-200 rounded-lg p-3.5">
            <div className="text-[10px] uppercase font-semibold text-neutral-400">
              Networks Modeled
            </div>
            <div className="text-lg font-semibold text-neutral-900 mt-0.5">
              {metrics.networks_modeled}
            </div>
          </div>
          <div className="bg-white border border-neutral-200 rounded-lg p-3.5">
            <div className="text-[10px] uppercase font-semibold text-neutral-400">
              Rules Evaluated
            </div>
            <div className="text-lg font-semibold text-neutral-900 mt-0.5">
              {metrics.requirements_evaluated}
            </div>
          </div>
          <div className="bg-white border border-neutral-200 rounded-lg p-3.5">
            <div className="text-[10px] uppercase font-semibold text-neutral-400">
              Verified (Pass)
            </div>
            <div className="text-lg font-semibold text-emerald-700 mt-0.5">
              {metrics.requirements_verified}
            </div>
          </div>
          <div className="bg-white border border-neutral-200 rounded-lg p-3.5">
            <div className="text-[10px] uppercase font-semibold text-neutral-400">
              Discrepancies
            </div>
            <div className="text-lg font-semibold text-neutral-900 mt-0.5">
              {metrics.model_discrepancies}
            </div>
          </div>
          <div className="bg-white border border-neutral-200 rounded-lg p-3.5">
            <div className="text-[10px] uppercase font-semibold text-neutral-400">
              Last Run Time
            </div>
            <div className="text-lg font-semibold text-neutral-900 mt-0.5">
              {metrics.last_execution_duration_ms
                ? `${metrics.last_execution_duration_ms}ms`
                : "—"}
            </div>
          </div>
        </div>
      )}

      {/* Live System Status Strip */}
      <div className="bg-white border border-neutral-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
            System Readiness & Diagnostics
          </h2>
          <Link
            href="/settings"
            className="text-xs text-blue-600 hover:underline flex items-center gap-1"
          >
            Inspect Settings <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {error ? (
          <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-3">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>
              Backend API unreachable ({error}). Start FastAPI on port 8000.
            </span>
          </div>
        ) : !health ? (
          <div className="text-xs text-neutral-400">
            Checking backend services...
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-3 rounded-md bg-neutral-50 border border-neutral-200/80 flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5" />
              <div>
                <div className="text-xs font-medium text-neutral-900">
                  Twin Engine API & SQLite
                </div>
                <div className="text-[11px] text-neutral-500">
                  v{health.version} · Connected
                </div>
              </div>
            </div>

            <div className="p-3 rounded-md bg-neutral-50 border border-neutral-200/80 flex items-start gap-2.5">
              <Sparkles className="h-4 w-4 text-blue-600 mt-0.5" />
              <div>
                <div className="text-xs font-medium text-neutral-900">
                  Gemma 4 Intent Adapter
                </div>
                <div className="text-[11px] text-neutral-500">
                  Mode: {health.gemma_provider} ({health.gemma_model})
                </div>
              </div>
            </div>

            <div className="p-3 rounded-md bg-neutral-50 border border-neutral-200/80 flex items-start gap-2.5">
              {health.docker_available ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5" />
              )}
              <div>
                <div className="text-xs font-medium text-neutral-900">
                  Isolated Docker Runner
                </div>
                <div className="text-[11px] text-neutral-500">
                  {health.docker_detail}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Three Pillar Workflow */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-neutral-200 rounded-lg p-5">
          <Boxes className="h-5 w-5 text-neutral-700 mb-2" />
          <h3 className="text-sm font-semibold text-neutral-900">
            1. Reconstruct Infrastructure Twin
          </h3>
          <p className="mt-1 text-xs text-neutral-600 leading-relaxed">
            Parses Docker Compose configurations into a multi-relationship graph distinguishing shared networks, orchestration dependencies, and published ports.
          </p>
        </div>

        <div className="bg-white border border-neutral-200 rounded-lg p-5">
          <Sparkles className="h-5 w-5 text-blue-600 mb-2" />
          <h3 className="text-sm font-semibold text-neutral-900">
            2. Propose & Simulate Counterfactuals
          </h3>
          <p className="mt-1 text-xs text-neutral-600 leading-relaxed">
            Gemma 4 translates natural-language security goals into schema-validated allow/deny rules. NetworkX evaluates graph reachability before execution.
          </p>
        </div>

        <div className="bg-white border border-neutral-200 rounded-lg p-5">
          <ShieldAlert className="h-5 w-5 text-emerald-600 mb-2" />
          <h3 className="text-sm font-semibold text-neutral-900">
            3. Verify in Disposable Sandbox
          </h3>
          <p className="mt-1 text-xs text-neutral-600 leading-relaxed">
            Runs bounded connectivity probes inside an isolated Docker network namespace and compares observed runtime evidence against simulation predictions.
          </p>
        </div>
      </div>
    </div>
  );
}