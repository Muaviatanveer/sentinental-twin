"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getExperiment, runExperiment } from "@/lib/api";
import { ExperimentResponse } from "@/lib/types";
import {
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Terminal,
  ShieldCheck,
  ArrowLeft,
  FileCheck2,
  Clock,
  Hash,
} from "lucide-react";

export default function ExperimentExecutionPage({
  params,
}: {
  params: { id: string; expId: string };
}) {
  const [experiment, setExperiment] = useState<ExperimentResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getExperiment(params.expId)
      .then(setExperiment)
      .catch((err) => setError(err.message));
  }, [params.expId]);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      const updated = await runExperiment(params.expId);
      setExperiment(updated);
    } catch (err: any) {
      setError(err.message);
      // Refresh state even on error to capture recorded error evidence
      getExperiment(params.expId)
        .then(setExperiment)
        .catch(() => null);
    } finally {
      setRunning(false);
    }
  };

  if (!experiment) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
      </div>
    );
  }

  const passedCount = experiment.test_cases.filter(
    (t) => t.observed === "pass"
  ).length;
  const discrepancyCount = experiment.test_cases.filter(
    (t) => t.discrepancy
  ).length;

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-200 pb-5">
        <div className="flex items-center gap-3">
          <Link
            href={`/projects/${params.id}/experiments/new`}
            className="p-1.5 rounded-md border border-neutral-200 text-neutral-600 hover:bg-neutral-50"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold text-neutral-900">
                Isolated Sandbox Verification
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-neutral-100 text-neutral-700 border border-neutral-200">
                {experiment.id}
              </span>
            </div>
            <p className="text-xs text-neutral-500 mt-0.5">
              Spins up an isolated Docker Compose namespace, runs bounded TCP connectivity probes, and tears down all containers automatically.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {experiment.status === "completed" && (
            <Link
              href={`/projects/${params.id}/reports/${experiment.id}`}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-medium bg-white border border-neutral-300 text-neutral-800 hover:bg-neutral-50"
            >
              <FileCheck2 className="h-3.5 w-3.5 text-emerald-600" />
              View Evidence Report
            </Link>
          )}

          <button
            onClick={handleRun}
            disabled={running}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-medium bg-neutral-900 text-white hover:bg-neutral-800 disabled:opacity-50"
          >
            {running ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Running Disposable Twin...
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 text-emerald-400" />
                {experiment.status === "completed"
                  ? "Re-Run Verification"
                  : "Execute Isolated Verification"}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Safeguards Banner */}
      <div className="bg-white border border-neutral-200 rounded-lg p-4 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2 text-neutral-700">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          <span className="font-medium">Sandbox Guardrails Active:</span>
          <span className="text-neutral-500">
            Host ports stripped · Volumes stripped · Privileged mode denied · Auto-teardown enabled
          </span>
        </div>
        <div className="flex items-center gap-4 text-neutral-500">
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            Duration:{" "}
            <strong className="text-neutral-800">
              {experiment.duration_ms ? `${experiment.duration_ms} ms` : "—"}
            </strong>
          </span>
          <span>
            Status:{" "}
            <strong className="uppercase text-neutral-900">
              {running ? "RUNNING" : experiment.status}
            </strong>
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-md bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Predicted vs. Observed Connectivity Matrix */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <div className="px-5 py-3.5 border-b border-neutral-200 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Predicted vs. Observed Connectivity Probes
          </h2>
          {experiment.status === "completed" && (
            <div className="flex items-center gap-3 text-xs">
              <span className="text-emerald-700 font-medium">
                {passedCount}/{experiment.test_cases.length} Requirements Verified
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                  discrepancyCount === 0
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-amber-50 text-amber-800 border border-amber-200"
                }`}
              >
                Model Discrepancies: {discrepancyCount}
              </span>
            </div>
          )}
        </div>

        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-neutral-200 bg-neutral-50/70 text-[11px] uppercase text-neutral-500">
              <th className="py-2.5 px-4">Probe Path</th>
              <th className="py-2.5 px-4">Policy Requirement</th>
              <th className="py-2.5 px-4">Graph Prediction</th>
              <th className="py-2.5 px-4">Observed Runtime</th>
              <th className="py-2.5 px-4">Exit Code</th>
              <th className="py-2.5 px-4">Verification Grade</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {experiment.test_cases.map((tc) => (
              <tr key={tc.id} className="hover:bg-neutral-50/50">
                <td className="py-3 px-4 font-mono font-medium text-neutral-900">
                  {tc.source} → {tc.destination}:{tc.target_port}
                </td>
                <td className="py-3 px-4">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      tc.expected === "allow"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-red-50 text-red-700 border border-red-200"
                    }`}
                  >
                    {tc.expected}
                  </span>
                </td>
                <td className="py-3 px-4 font-mono text-neutral-600 uppercase">
                  {tc.predicted}
                </td>
                <td className="py-3 px-4 font-mono">
                  {tc.actual_outcome ? (
                    <span
                      className={
                        tc.actual_outcome === "reachable"
                          ? "text-emerald-700 font-semibold"
                          : "text-red-700 font-semibold"
                      }
                    >
                      {tc.actual_outcome.toUpperCase()}
                    </span>
                  ) : (
                    <span className="text-neutral-400">NOT RUN</span>
                  )}
                </td>
                <td className="py-3 px-4 font-mono text-neutral-600">
                  {tc.exit_code !== null && tc.exit_code !== undefined
                    ? tc.exit_code
                    : "—"}
                </td>
                <td className="py-3 px-4">
                  {tc.observed === "pass" ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                      <CheckCircle2 className="h-3.5 w-3.5" /> VERIFIED PASS
                    </span>
                  ) : tc.observed === "fail" ? (
                    <span className="inline-flex items-center gap-1 text-red-600 font-semibold">
                      <XCircle className="h-3.5 w-3.5" /> FAILED
                    </span>
                  ) : (
                    <span className="text-neutral-400">Pending Execution</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Cryptographic Evidence & Raw Container Logs */}
      {experiment.evidence.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-500 flex items-center gap-1.5">
            <Terminal className="h-3.5 w-3.5" />
            Captured Runtime Evidence & SHA-256 Integrity Hashes
          </h2>
          {experiment.evidence.map((ev) => (
            <div
              key={ev.id}
              className="bg-white border border-neutral-200 rounded-lg overflow-hidden"
            >
              <div className="px-4 py-2.5 bg-neutral-50 border-b border-neutral-200 flex items-center justify-between text-xs">
                <span className="font-mono font-semibold text-neutral-800">
                  {ev.kind}
                </span>
                <span className="font-mono text-[11px] text-neutral-500 flex items-center gap-1">
                  <Hash className="h-3 w-3" />
                  SHA-256: {ev.content_hash.slice(0, 24)}...
                </span>
              </div>
              <pre className="p-4 bg-neutral-900 text-neutral-100 font-mono text-[11px] overflow-x-auto leading-relaxed">
                {ev.content}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
