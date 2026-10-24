"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getProjectTopology } from "@/lib/api";
import { ServiceNode, TopologyGraph } from "@/lib/types";
import { TopologyCanvas } from "@/components/topology/TopologyCanvas";
import {
    Loader2,
    AlertTriangle,
    Info,
    Sparkles,
    X,
    Server,
} from "lucide-react";

export default function TopologyPage({ params }: { params: { id: string } }) {
    const [topology, setTopology] = useState<TopologyGraph | null>(null);
    const [selectedSvc, setSelectedSvc] = useState<ServiceNode | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        getProjectTopology(params.id)
            .then(setTopology)
            .catch((err) => setError(err.message));
    }, [params.id]);

    if (error) {
        return (
            <div className="p-8">
                <div className="flex items-center gap-2 text-red-600 bg-red-50 p-4 rounded-md border border-red-200">
                    <AlertTriangle className="h-5 w-5" />
                    <span className="text-sm font-medium">{error}</span>
                </div>
            </div>
        );
    }

    if (!topology) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
            </div>
        );
    }

    const handleSelectService = (svcName: string) => {
        const found = topology.services.find((s) => s.name === svcName) || null;
        setSelectedSvc(found);
    };

    return (
        <div className="flex flex-col h-screen w-full">
            {/* Header Bar */}
            <div className="shrink-0 bg-white border-b border-neutral-200 px-6 py-4 flex items-center justify-between">
                <div>
                    <h1 className="text-lg font-semibold text-neutral-900 flex items-center gap-2">
                        Baseline Infrastructure Topology
                        <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-neutral-100 text-neutral-600 border border-neutral-200 tracking-wider">
                            Snapshot G0
                        </span>
                    </h1>
                    <p className="text-xs text-neutral-500 mt-1">
                        {topology.services.length} Services · {topology.networks.length}{" "}
                        Networks · Click any node to inspect configuration
                    </p>
                </div>

                <Link
                    href={`/projects/${params.id}/experiments/new`}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-900 text-white text-xs font-medium rounded-md hover:bg-neutral-800 transition-colors"
                >
                    <Sparkles className="h-3.5 w-3.5 text-blue-400" />
                    Propose Security Experiment
                </Link>
            </div>

            {/* Warnings Panel */}
            {topology.warnings.length > 0 && (
                <div className="shrink-0 bg-amber-50/60 border-b border-amber-200/60 px-6 py-2 flex gap-3 overflow-x-auto">
                    {topology.warnings.map((w, i) => (
                        <div
                            key={i}
                            className="flex items-center gap-1.5 whitespace-nowrap text-[11px] text-amber-800 bg-amber-100/70 px-2.5 py-1 rounded"
                        >
                            <Info className="h-3 w-3 shrink-0" />
                            {w}
                        </div>
                    ))}
                </div>
            )}

            {/* Main Canvas + Optional Inspector Drawer */}
            <div className="flex-1 flex relative overflow-hidden">
                <div className="flex-1 relative">
                    <TopologyCanvas
                        topology={topology}
                        onSelectService={handleSelectService}
                    />
                </div>

                {selectedSvc && (
                    <div className="w-80 bg-white border-l border-neutral-200 p-5 overflow-y-auto space-y-4">
                        <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
                            <div className="flex items-center gap-2">
                                <Server className="h-4 w-4 text-blue-600" />
                                <span className="text-sm font-semibold text-neutral-900">
                                    {selectedSvc.name}
                                </span>
                            </div>
                            <button
                                onClick={() => setSelectedSvc(null)}
                                className="text-neutral-400 hover:text-neutral-700"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>

                        <div className="space-y-3 text-xs">
                            <div>
                                <div className="text-[10px] uppercase font-semibold text-neutral-400">
                                    Container Image
                                </div>
                                <div className="font-mono text-neutral-800 mt-0.5">
                                    {selectedSvc.image || "N/A"}
                                </div>
                            </div>

                            <div>
                                <div className="text-[10px] uppercase font-semibold text-neutral-400">
                                    Attached Networks
                                </div>
                                <div className="flex flex-wrap gap-1 mt-1">
                                    {selectedSvc.networks.map((n) => (
                                        <span
                                            key={n}
                                            className="px-2 py-0.5 bg-neutral-100 border border-neutral-200 rounded text-[11px]"
                                        >
                                            {n}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <div className="text-[10px] uppercase font-semibold text-neutral-400">
                                    Baseline Reachability From {selectedSvc.name}
                                </div>
                                <div className="mt-1 space-y-1">
                                    {Object.entries(
                                        topology.reachability_matrix[selectedSvc.name] || {}
                                    ).map(([target, status]) => (
                                        <div
                                            key={target}
                                            className="flex items-center justify-between py-1 px-2 bg-neutral-50 rounded border border-neutral-100"
                                        >
                                            <span className="font-medium">→ {target}</span>
                                            <span className="text-[10px] font-mono text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                                                {status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}