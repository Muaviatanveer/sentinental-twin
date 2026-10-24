"use client";

import { useEffect, useMemo } from "react";
import {
    ReactFlow,
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    EdgeTypes,
    NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { TopologyGraph } from "@/lib/types";
import { ServiceNodeComponent } from "./ServiceNodeComponent";

interface Props {
    topology: TopologyGraph;
    onSelectService?: (serviceName: string) => void;
}

export function TopologyCanvas({ topology, onSelectService }: Props) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    const nodeTypes: NodeTypes = useMemo(
        () => ({ serviceNode: ServiceNodeComponent }),
        []
    );
    const edgeTypes: EdgeTypes = useMemo(() => ({}), []);

    useEffect(() => {
        const newNodes = topology.services.map((svc, index) => ({
            id: svc.id,
            type: "serviceNode",
            position: {
                x: (index % 3) * 290 + 60,
                y: Math.floor(index / 3) * 220 + 80,
            },
            data: {
                label: svc.name,
                networks: svc.networks,
                ports: svc.published_ports,
            },
        }));

        const newEdges = topology.edges.map((edge) => {
            const isSharedNet = edge.relationship === "shares_network";
            const isBlocked = edge.diff_status === "newly_blocked";
            const isNewPermit = edge.diff_status === "newly_permitted";

            let strokeColor = isSharedNet ? "#2563eb" : "#a3a3a3";
            let strokeDasharray: string | undefined = isSharedNet ? undefined : "5 5";
            let edgeLabel = isSharedNet
                ? (edge.metadata?.networks as string[])?.join(", ") || "shared net"
                : edge.label;

            if (isBlocked) {
                strokeColor = "#dc2626";
                strokeDasharray = "6 4";
                edgeLabel = "BLOCKED BY POLICY";
            } else if (isNewPermit) {
                strokeColor = "#16a34a";
                edgeLabel = `NEW: ${(edge.metadata?.networks as string[])?.join(", ")}`;
            }

            return {
                id: edge.id,
                source: edge.source,
                target: edge.target,
                label: edgeLabel,
                animated: isSharedNet && !isBlocked,
                labelStyle: {
                    fontSize: 10,
                    fontWeight: 600,
                    fill: isBlocked ? "#dc2626" : "#404040",
                },
                style: {
                    stroke: strokeColor,
                    strokeWidth: isBlocked ? 2.5 : isSharedNet ? 2 : 1.2,
                    strokeDasharray,
                },
            };
        });

        setNodes(newNodes as any);
        setEdges(newEdges as any);
    }, [topology, setNodes, setEdges]);

    return (
        <div className="w-full h-full bg-[#FAFAFA]">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(_, node: any) =>
                    onSelectService && onSelectService(node.data?.label)
                }
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                fitView
                fitViewOptions={{ padding: 0.25 }}
                proOptions={{ hideAttribution: true }}
            >
                <Background color="#E5E5E5" gap={20} size={1} />
                <Controls showInteractive={false} />
            </ReactFlow>
        </div>
    );
}