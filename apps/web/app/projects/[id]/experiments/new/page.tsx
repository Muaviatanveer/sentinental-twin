"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
    getProjectTopology,
    generateProposal,
    validateProposal,
    simulateProposal,
    createExperiment,
} from "@/lib/api";
import {
    PolicyRequirement,
    ProposalResponse,
    SimulationResponse,
    TopologyGraph,
} from "@/lib/types";
import { TopologyCanvas } from "@/components/topology/TopologyCanvas";
import {
    Sparkles,
    CheckCircle2,
    AlertTriangle,
    Play,
    Plus,
    Trash2,
    ArrowLeft,
    Loader2,
    FileCode2,
    ShieldCheck,
} from "lucide-react";

const DEFAULT_INTENT =
    "Allow the frontend to communicate with the api, but prevent the frontend from accessing the database directly. Keep api to database communication working.";

export default function ExperimentBuilderPage({
    params,
}: {
    params: { id: string };
}) {
    const router = useRouter();

    const handleApproveForTesting = async () => {
        if (!proposal) return;
        try {
            const exp = await createExperiment(params.id, proposal.id);
            router.push(`/projects/${params.id}/experiments/${exp.id}`);
        } catch (err: any) {
            setErrorMsg(err.message);
        }
    };

    const [baseline, setBaseline] = useState<TopologyGraph | null>(null);
    const [intent, setIntent] = useState(DEFAULT_INTENT);
    const [proposal, setProposal] = useState<ProposalResponse | null>(null);
    const [requirements, setRequirements] = useState<PolicyRequirement[]>([]);
    const [simulation, setSimulation] = useState<SimulationResponse | null>(null);

    const [viewMode, setViewMode] = useState<"candidate" | "baseline" | "diff">(
        "candidate"
    );
    const [stage, setStage] = useState<
        "idle" | "generating" | "validating" | "simulating" | "ready" | "error"
    >("idle");
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    useEffect(() => {
        getProjectTopology(params.id)
            .then(setBaseline)
            .catch((err) => setErrorMsg(err.message));
    }, [params.id]);

    const handleGenerateProposal = async () => {
        setStage("generating");
        setErrorMsg(null);
        setSimulation(null);
        try {
            const prop = await generateProposal(params.id, intent);
            setProposal(prop);
            setRequirements(prop.requirements);
            setStage("ready");
        } catch (err: any) {
            setErrorMsg(err.message);
            setStage("error");
        }
    };

    const handleValidate = async () => {
        if (!proposal) return;
        setStage("validating");
        setErrorMsg(null);
        try {
            const updated = await validateProposal(
                params.id,
                proposal.id,
                requirements
            );
            setProposal(updated);
            setStage("ready");
        } catch (err: any) {
            setErrorMsg(err.message);
            setStage("error");
        }
    };

    const handleSimulate = async () => {
        if (!proposal) return;
        setStage("simulating");
        setErrorMsg(null);
        try {
            const sim = await simulateProposal(params.id, proposal.id, requirements);
            setSimulation(sim);
            setViewMode("candidate");
            setStage("ready");
        } catch (err: any) {
            setErrorMsg(err.message);
            setStage("error");
        }
    };

    const updateRequirement = (
        idx: number,
        field: keyof PolicyRequirement,
        value: string
    ) => {
        const copy = [...requirements];
        copy[idx] = { ...copy[idx], [field]: value as any };
        setRequirements(copy);
    };

    const addRequirement = () => {
        const svcs = baseline?.services.map((s) => s.name) || ["frontend", "api"];
        setRequirements([
            ...requirements,
            {
                source: svcs[0] || "frontend",
                destination: svcs[1] || "database",
                expected: "deny",
            },
        ]);
    };

    const removeRequirement = (idx: number) => {
        setRequirements(requirements.filter((_, i) => i !== idx));
    };

    return (
        <div className="flex flex-col h-screen w-full overflow-hidden">
            {/* Top Bar */}
            <div className="shrink-0 bg-white border-b border-neutral-200 px-6 py-3.5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Link
                        href={`/projects/${params.id}/topology`}
                        className="p-1.5 rounded-md border border-neutral-200 text-neutral-600 hover:bg-neutral-50"
                    >
                        <ArrowLeft className="h-4 w-4" />
                    </Link>
                    <div>
                        <h1 className="text-base font-semibold text-neutral-900">
                            Counterfactual Security Experiment Builder
                        </h1>
                        <p className="text-xs text-neutral-500">
                            Translate natural-language boundaries with Gemma 4 and simulate graph reachability before container execution.
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2 text-xs">
                    <span className="px-2.5 py-1 rounded-full font-medium bg-neutral-100 text-neutral-700 border border-neutral-200">
                        State: {stage.toUpperCase()}
                    </span>
                </div>
            </div>

            {/* Main Split Workspace */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 overflow-hidden">
                {/* Left Column: Intent & Policy Editor */}
                <div className="lg:col-span-5 border-r border-neutral-200 bg-white overflow-y-auto p-6 space-y-6">
                    {/* 1. Natural Language Intent */}
                    <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-neutral-500 flex items-center gap-1.5">
                            <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                            1. Describe Desired Security Boundary (Gemma 4)
                        </label>
                        <textarea
                            rows={3}
                            value={intent}
                            onChange={(e) => setIntent(e.target.value)}
                            className="w-full rounded-md border border-neutral-300 p-3 text-xs text-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="e.g., Prevent frontend from accessing database directly..."
                        />
                        <div className="flex items-center justify-between pt-1">
                            <button
                                type="button"
                                onClick={() =>
                                    setIntent(
                                        "Block frontend from talking to redis_cache directly."
                                    )
                                }
                                className="text-[11px] text-neutral-500 hover:text-neutral-800 underline"
                            >
                                Test Invalid Service Rejection
                            </button>
                            <button
                                onClick={handleGenerateProposal}
                                disabled={stage === "generating"}
                                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-medium bg-neutral-900 text-white hover:bg-neutral-800 disabled:opacity-50"
                            >
                                {stage === "generating" ? (
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : (
                                    <Sparkles className="h-3.5 w-3.5 text-blue-400" />
                                )}
                                Generate Proposal
                            </button>
                        </div>
                    </div>

                    {errorMsg && (
                        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2">
                            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                            <span>{errorMsg}</span>
                        </div>
                    )}

                    {/* 2. Structured Requirements Editor */}
                    {proposal && (
                        <div className="space-y-4 border-t border-neutral-200 pt-5">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                                        2. Review & Edit Structured Policy Proposal
                                    </h2>
                                    <p className="text-[11px] text-neutral-500 mt-0.5">
                                        Reason: {proposal.reason}
                                    </p>
                                </div>
                                <span
                                    className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${proposal.status === "rejected"
                                            ? "bg-red-50 text-red-700 border border-red-200"
                                            : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                        }`}
                                >
                                    {proposal.status}
                                </span>
                            </div>

                            {/* Gemma 4 26B A4B Thinking Mode & Telemetry Card */}
                            <div className="p-3.5 rounded-lg bg-blue-50/50 border border-blue-200/80 space-y-2.5 text-xs">
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                    <span className="inline-flex items-center gap-1.5 font-semibold text-blue-900">
                                        <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                                        Gemma 4 26B A4B (MoE) Reasoning Trace
                                    </span>
                                    <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-white border border-blue-200 text-blue-800">
                                        {proposal.provider_used} · {proposal.model_used} ·{" "}
                                        {proposal.latency_ms}ms
                                    </span>
                                </div>

                                {proposal.risk_assessment && (
                                    <div className="text-[11px] text-neutral-800 bg-white/90 p-2.5 rounded border border-blue-100">
                                        <strong className="text-neutral-900">
                                            Baseline Risk Assessment:{" "}
                                        </strong>
                                        {proposal.risk_assessment}
                                    </div>
                                )}

                                {proposal.thinking_trace && proposal.thinking_trace.length > 0 && (
                                    <div className="space-y-1.5">
                                        <div className="text-[10px] font-semibold uppercase tracking-wider text-blue-700">
                                            Step-by-Step Thinking Mode Chain:
                                        </div>
                                        <ol className="space-y-1 text-[11px] text-neutral-700 list-decimal list-inside bg-white/80 p-2.5 rounded border border-blue-100">
                                            {proposal.thinking_trace.map((step, i) => (
                                                <li key={i} className="leading-relaxed">
                                                    {step}
                                                </li>
                                            ))}
                                        </ol>
                                    </div>
                                )}

                                {proposal.raw_output && (
                                    <details className="text-[11px]">
                                        <summary className="cursor-pointer font-medium text-blue-700 hover:underline">
                                            Inspect Raw Gemma 4 Structured JSON Output
                                        </summary>
                                        <pre className="mt-1.5 p-2.5 rounded bg-neutral-900 text-emerald-400 font-mono text-[10px] overflow-x-auto">
                                            {proposal.raw_output}
                                        </pre>
                                    </details>
                                )}
                            </div>

                            {/* Validation Errors */}
                            {proposal.validation_errors.length > 0 && (
                                <div className="p-3 rounded-md bg-red-50 border border-red-200 space-y-1">
                                    <div className="text-xs font-semibold text-red-800 flex items-center gap-1.5">
                                        <AlertTriangle className="h-3.5 w-3.5" />
                                        Semantic Validation Blocked Proposal:
                                    </div>
                                    <ul className="list-disc list-inside text-[11px] text-red-700 space-y-0.5">
                                        {proposal.validation_errors.map((err, i) => (
                                            <li key={i}>{err}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Editable Requirement Rows */}
                            <div className="space-y-2">
                                {requirements.map((req, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-center gap-2 p-2 rounded-md bg-neutral-50 border border-neutral-200 text-xs"
                                    >
                                        <input
                                            value={req.source}
                                            onChange={(e) =>
                                                updateRequirement(idx, "source", e.target.value)
                                            }
                                            className="w-28 px-2 py-1 bg-white border border-neutral-300 rounded font-mono text-xs"
                                            placeholder="source"
                                        />
                                        <span className="text-neutral-400">→</span>
                                        <input
                                            value={req.destination}
                                            onChange={(e) =>
                                                updateRequirement(idx, "destination", e.target.value)
                                            }
                                            className="w-28 px-2 py-1 bg-white border border-neutral-300 rounded font-mono text-xs"
                                            placeholder="destination"
                                        />
                                        <select
                                            value={req.expected}
                                            onChange={(e) =>
                                                updateRequirement(idx, "expected", e.target.value)
                                            }
                                            className={`px-2 py-1 rounded font-semibold text-xs border ${req.expected === "allow"
                                                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                                    : "bg-red-50 text-red-700 border-red-200"
                                                }`}
                                        >
                                            <option value="allow">ALLOW</option>
                                            <option value="deny">DENY</option>
                                        </select>
                                        <button
                                            onClick={() => removeRequirement(idx)}
                                            className="ml-auto text-neutral-400 hover:text-red-600 p-1"
                                        >
                                            <Trash2 className="h-3.5 w-3.5" />
                                        </button>
                                    </div>
                                ))}

                                <button
                                    onClick={addRequirement}
                                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline pt-1"
                                >
                                    <Plus className="h-3.5 w-3.5" /> Add Rule
                                </button>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-2.5 pt-2">
                                <button
                                    onClick={handleValidate}
                                    disabled={stage === "validating"}
                                    className="px-3 py-2 rounded-md border border-neutral-300 bg-white text-neutral-800 text-xs font-medium hover:bg-neutral-50"
                                >
                                    Validate Proposal
                                </button>
                                <button
                                    onClick={handleSimulate}
                                    disabled={stage === "simulating"}
                                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-blue-600 text-white text-xs font-medium hover:bg-blue-700"
                                >
                                    {stage === "simulating" ? (
                                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    ) : (
                                        <Play className="h-3.5 w-3.5" />
                                    )}
                                    Preview Counterfactual Impact
                                </button>
                            </div>
                        </div>
                    )}

                    {/* 3. Simulation Impact Summary */}
                    {simulation && (
                        <div className="space-y-4 border-t border-neutral-200 pt-5">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                                    3. Predicted Reachability Impact (ΔG = G1 - G0)
                                </h2>
                                <span className="text-[10px] px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                                    Simulated · Not Yet Executed
                                </span>
                            </div>

                            <div className="space-y-2">
                                {simulation.impacts.map((imp, idx) => (
                                    <div
                                        key={idx}
                                        className="p-3 rounded-md border border-neutral-200 bg-neutral-50/70 text-xs space-y-1"
                                    >
                                        <div className="flex items-center justify-between font-medium">
                                            <span>
                                                {imp.source} → {imp.destination}
                                            </span>
                                            <span
                                                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${imp.change_type === "newly_blocked"
                                                        ? "bg-red-100 text-red-700"
                                                        : imp.change_type === "unchanged"
                                                            ? "bg-emerald-100 text-emerald-700"
                                                            : "bg-amber-100 text-amber-800"
                                                    }`}
                                            >
                                                {imp.change_type.replace("_", " ")}
                                            </span>
                                        </div>
                                        <div className="text-[11px] text-neutral-500">
                                            Baseline:{" "}
                                            <code className="text-neutral-700">
                                                {imp.baseline_state}
                                            </code>{" "}
                                            → Candidate:{" "}
                                            <code className="text-neutral-900 font-semibold">
                                                {imp.candidate_state}
                                            </code>
                                        </div>
                                        <div className="text-[11px] text-neutral-500">
                                            {imp.rule_applied}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Column: Visual Topology Diff & Candidate YAML Diff */}
                <div className="lg:col-span-7 flex flex-col min-h-0 bg-[#FAFAFA]">
                    {/* View Switcher Bar */}
                    <div className="shrink-0 bg-white border-b border-neutral-200 px-5 py-2.5 flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                            <button
                                onClick={() => setViewMode("candidate")}
                                className={`px-3 py-1 rounded text-xs font-medium ${viewMode === "candidate"
                                        ? "bg-neutral-900 text-white"
                                        : "text-neutral-600 hover:bg-neutral-100"
                                    }`}
                            >
                                Candidate Diff Graph (G1)
                            </button>
                            <button
                                onClick={() => setViewMode("baseline")}
                                className={`px-3 py-1 rounded text-xs font-medium ${viewMode === "baseline"
                                        ? "bg-neutral-900 text-white"
                                        : "text-neutral-600 hover:bg-neutral-100"
                                    }`}
                            >
                                Baseline Graph (G0)
                            </button>
                            <button
                                onClick={() => setViewMode("diff")}
                                disabled={!simulation}
                                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium disabled:opacity-40 ${viewMode === "diff"
                                        ? "bg-neutral-900 text-white"
                                        : "text-neutral-600 hover:bg-neutral-100"
                                    }`}
                            >
                                <FileCode2 className="h-3.5 w-3.5" />
                                Compose YAML Diff
                            </button>
                        </div>

                        {simulation && (
                            <button
                                onClick={handleApproveForTesting}
                                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700 transition-colors"
                            >
                                <ShieldCheck className="h-3.5 w-3.5" />
                                Approve for Sandbox Testing
                            </button>
                        )}
                    </div>

                    {/* Canvas or Diff Viewer */}
                    <div className="flex-1 relative overflow-auto">
                        {viewMode === "diff" && simulation ? (
                            <div className="p-6 space-y-4">
                                <div className="bg-neutral-900 text-neutral-100 rounded-lg p-4 font-mono text-xs overflow-x-auto leading-relaxed">
                                    {simulation.yaml_diff.split("\n").map((line, i) => {
                                        let color = "text-neutral-300";
                                        if (line.startsWith("+")) color = "text-emerald-400";
                                        if (line.startsWith("-")) color = "text-red-400";
                                        if (line.startsWith("@@")) color = "text-blue-400";
                                        return (
                                            <div key={i} className={color}>
                                                {line}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            baseline && (
                                <TopologyCanvas
                                    topology={
                                        viewMode === "candidate" && simulation
                                            ? simulation.candidate_topology
                                            : baseline
                                    }
                                />
                            )
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}