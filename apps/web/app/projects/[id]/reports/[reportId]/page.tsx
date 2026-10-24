"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getExperimentReport } from "@/lib/api";
import { VerificationReportResponse } from "@/lib/types";
import {
  Download,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  ShieldAlert,
  FileCode2,
  Loader2,
  Hash,
} from "lucide-react";

export default function VerificationReportPage({
  params,
}: {
  params: { id: string; reportId: string };
}) {
  const [report, setReport] = useState<VerificationReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getExperimentReport(params.reportId)
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [params.reportId]);

  const downloadFile = (filename: string, content: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (error) {
    return <div className="p-8 text-xs text-red-600">{error}</div>;
  }

  if (!report) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-200 pb-5">
        <div className="flex items-center gap-3">
          <Link
            href={`/projects/${params.id}/experiments/${report.experiment_id}`}
            className="p-1.5 rounded-md border border-neutral-200 text-neutral-600 hover:bg-neutral-50"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold text-neutral-900">
                Evidence & Change Verification Report
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                {report.report_id}
              </span>
            </div>
            <p className="text-xs text-neutral-500 mt-0.5">
              Intent: &ldquo;{report.intent}&rdquo;
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() =>
              downloadFile(
                `sentinel-report-${report.experiment_id}.md`,
                report.markdown_report,
                "text/markdown"
              )
            }
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-neutral-300 bg-white text-neutral-800 text-xs font-medium hover:bg-neutral-50"
          >
            <Download className="h-3.5 w-3.5" />
            Export Markdown
          </button>
          <button
            onClick={() =>
              downloadFile(
                `sentinel-report-${report.experiment_id}.json`,
                JSON.stringify(report, null, 2),
                "application/json"
              )
            }
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-neutral-300 bg-white text-neutral-800 text-xs font-medium hover:bg-neutral-50"
          >
            <Download className="h-3.5 w-3.5" />
            Export JSON
          </button>
          <button
            onClick={() =>
              downloadFile(
                "compose.candidate.yaml",
                report.candidate_yaml,
                "text/yaml"
              )
            }
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md bg-neutral-900 text-white text-xs font-medium hover:bg-neutral-800"
          >
            <FileCode2 className="h-3.5 w-3.5" />
            Export Candidate compose.yaml
          </button>
        </div>
      </div>

      {/* Section 17 Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-[11px] text-neutral-500 uppercase font-semibold">
            Requirements Verified
          </div>
          <div className="text-xl font-semibold text-emerald-700 mt-1">
            {report.verified_passed} / {report.total_requirements}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-[11px] text-neutral-500 uppercase font-semibold">
            Regressions Detected
          </div>
          <div className="text-xl font-semibold text-neutral-900 mt-1">
            {report.regressions_detected}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-[11px] text-neutral-500 uppercase font-semibold">
            Model Discrepancies
          </div>
          <div className="text-xl font-semibold text-neutral-900 mt-1">
            {report.model_discrepancies}
          </div>
        </div>
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <div className="text-[11px] text-neutral-500 uppercase font-semibold">
            Execution Duration
          </div>
          <div className="text-xl font-semibold text-neutral-900 mt-1">
            {report.duration_ms ? `${report.duration_ms} ms` : "—"}
          </div>
        </div>
      </div>

      {/* Configuration Hashes */}
      <div className="bg-white border border-neutral-200 rounded-lg p-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="flex items-center gap-2 font-mono text-neutral-600 truncate">
          <Hash className="h-3.5 w-3.5 shrink-0 text-neutral-400" />
          <span>Baseline SHA-256: {report.baseline_hash.slice(0, 32)}...</span>
        </div>
        <div className="flex items-center gap-2 font-mono text-neutral-600 truncate">
          <Hash className="h-3.5 w-3.5 shrink-0 text-neutral-400" />
          <span>Candidate SHA-256: {report.candidate_hash.slice(0, 32)}...</span>
        </div>
      </div>

      {/* Evidence Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <div className="px-5 py-3 border-b border-neutral-200 text-xs font-semibold uppercase tracking-wider text-neutral-500">
          Observed Runtime Evidence vs. Graph Simulation
        </div>
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-neutral-200 bg-neutral-50 text-[11px] uppercase text-neutral-500">
              <th className="py-2.5 px-4">Test Case</th>
              <th className="py-2.5 px-4">Expected</th>
              <th className="py-2.5 px-4">Graph Prediction</th>
              <th className="py-2.5 px-4">Observed Runtime</th>
              <th className="py-2.5 px-4">Exit Code</th>
              <th className="py-2.5 px-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {report.test_cases.map((tc) => (
              <tr key={tc.id}>
                <td className="py-3 px-4 font-mono font-medium">
                  {tc.source} → {tc.destination}:{tc.target_port}
                </td>
                <td className="py-3 px-4 uppercase font-semibold">
                  {tc.expected}
                </td>
                <td className="py-3 px-4 uppercase font-mono">
                  {tc.predicted}
                </td>
                <td className="py-3 px-4 uppercase font-mono font-semibold">
                  {tc.actual_outcome}
                </td>
                <td className="py-3 px-4 font-mono">{tc.exit_code}</td>
                <td className="py-3 px-4">
                  {tc.observed === "pass" ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                      <CheckCircle2 className="h-3.5 w-3.5" /> PASS
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-red-600 font-semibold">
                      <XCircle className="h-3.5 w-3.5" /> FAIL
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Unified Configuration Diff */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <div className="px-5 py-3 border-b border-neutral-200 text-xs font-semibold uppercase tracking-wider text-neutral-500">
          Candidate Configuration Patch (compose.yaml)
        </div>
        <pre className="p-4 bg-neutral-900 text-neutral-100 font-mono text-xs overflow-x-auto leading-relaxed">
          {report.yaml_diff}
        </pre>
      </div>

      {/* Explicit Limitations */}
      <div className="bg-amber-50/70 border border-amber-200 rounded-lg p-4 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-amber-900">
          <ShieldAlert className="h-4 w-4 text-amber-700" />
          Explicit Verification Boundaries & Limitations
        </div>
        <ul className="list-disc list-inside text-xs text-amber-800 space-y-1">
          {report.limitations.map((lim, i) => (
            <li key={i}>{lim}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
