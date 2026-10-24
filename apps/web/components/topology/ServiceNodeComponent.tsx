import { Handle, Position } from "@xyflow/react";
import { Box } from "lucide-react";

export function ServiceNodeComponent({ data }: any) {
    return (
        <div className="bg-white border border-neutral-300 rounded-lg shadow-sm w-[220px] font-sans text-neutral-900 flex flex-col overflow-hidden">
            {/* Target Handle (Incoming edges) */}
            <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-neutral-400 border-none" />

            {/* Header */}
            <div className="flex items-center gap-2 p-3 border-b border-neutral-100 bg-neutral-50/50">
                <Box className="h-4 w-4 text-blue-600 shrink-0" />
                <div className="font-medium text-sm truncate">{data.label}</div>
            </div>

            {/* Details */}
            <div className="p-3 space-y-3 bg-white">
                {/* Networks */}
                <div>
                    <div className="text-[10px] uppercase tracking-wider text-neutral-400 font-semibold mb-1.5">
                        Networks
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {data.networks?.map((net: string) => (
                            <span key={net} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-neutral-100 text-neutral-600 border border-neutral-200">
                                {net}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Ports */}
                {data.ports && data.ports.length > 0 && (
                    <div>
                        <div className="text-[10px] uppercase tracking-wider text-neutral-400 font-semibold mb-1.5">
                            Exposed Ports
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {data.ports.map((port: any, idx: number) => (
                                <span key={idx} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-100">
                                    {port.published ? `${port.host_port}->${port.container_port}` : port.container_port}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Source Handle (Outgoing edges) */}
            <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-neutral-400 border-none" />
        </div>
    );
}