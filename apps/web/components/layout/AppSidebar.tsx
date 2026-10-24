"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    Network,
    FlaskConical,
    FileCheck2,
    Settings,
    LayoutDashboard,
    FolderPlus,
    ShieldCheck,
} from "lucide-react";

const navItems = [
    { href: "/", label: "Overview", icon: LayoutDashboard },
    { href: "/projects/new", label: "Import Compose", icon: FolderPlus },
    { href: "/settings", label: "Diagnostics & Settings", icon: Settings },
];

export function AppSidebar() {
    const pathname = usePathname();

    return (
        <aside className="w-64 shrink-0 border-r border-neutral-200 bg-white flex flex-col justify-between min-h-screen">
            <div>
                <div className="p-5 border-b border-neutral-200">
                    <div className="flex items-center gap-2.5">
                        <div className="h-8 w-8 rounded-md bg-neutral-900 text-white flex items-center justify-center">
                            <ShieldCheck className="h-4 w-4" />
                        </div>
                        <div>
                            <div className="text-sm font-semibold tracking-tight text-neutral-900">
                                NeuroSyn Sentinel
                            </div>
                            <div className="text-[11px] text-neutral-500">
                                Infrastructure Twin v0.1
                            </div>
                        </div>
                    </div>
                </div>

                <div className="px-3 py-4">
                    <div className="px-2 pb-2 text-[11px] font-medium uppercase tracking-wider text-neutral-400">
                        Workspace
                    </div>
                    <nav className="space-y-1">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = pathname === item.href;
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md text-xs font-medium transition-colors ${isActive
                                            ? "bg-blue-50 text-blue-700 border border-blue-200/60"
                                            : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
                                        }`}
                                >
                                    <Icon className="h-4 w-4" />
                                    {item.label}
                                </Link>
                            );
                        })}
                    </nav>
                </div>

                <div className="px-3 py-2 border-t border-neutral-100">
                    <div className="px-2 pb-2 text-[11px] font-medium uppercase tracking-wider text-neutral-400">
                        Workflow Stages
                    </div>
                    <div className="space-y-1.5 px-2 text-xs text-neutral-500">
                        <div className="flex items-center gap-2">
                            <Network className="h-3.5 w-3.5 text-neutral-400" />
                            <span>1. Baseline Topology</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <FlaskConical className="h-3.5 w-3.5 text-neutral-400" />
                            <span>2. Gemma 4 Counterfactual</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <FileCheck2 className="h-3.5 w-3.5 text-neutral-400" />
                            <span>3. Isolated Verification</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-4 border-t border-neutral-200 bg-neutral-50/60 text-[11px] text-neutral-500">
                <div className="font-medium text-neutral-700">Safety Boundary Active</div>
                <div className="mt-0.5">
                    Disposable test twin only. No automatic production changes.
                </div>
            </div>
        </aside>
    );
}