from typing import Any
import uuid
from apps.api.app.schemas.contracts import (
    ServiceNode, NetworkNode, RelationshipEdge, PortMapping, TopologyGraph
)

class TwinBuilder:
    @staticmethod
    def build_topology(project_id: str, parsed_data: dict[str, Any]) -> TopologyGraph:
        raw_services = parsed_data["services"]
        raw_networks = parsed_data["networks"]
        
        services: list[ServiceNode] = []
        networks: list[NetworkNode] = []
        edges: list[RelationshipEdge] = []
        
        # 1. Build Network Nodes
        for net_name, net_def in raw_networks.items():
            net_def = net_def or {}
            networks.append(NetworkNode(
                id=f"net_{net_name}",
                name=net_name,
                internal=net_def.get("internal", False),
                driver=net_def.get("driver", "bridge")
            ))
            
        # 2. Build Service Nodes
        for svc_name, svc_def in raw_services.items():
            svc_id = f"svc_{svc_name}"
            
            # Networks fallback to 'default' if omitted
            svc_nets = svc_def.get("networks", ["default"])
            if isinstance(svc_nets, dict):
                svc_nets = list(svc_nets.keys())
                
            ports = []
            for port_def in svc_def.get("ports", []):
                # Simple parsing for "8000:8000" or just "8000"
                parts = str(port_def).split(":")
                if len(parts) >= 2:
                    ports.append(PortMapping(host_port=int(parts[0]), container_port=int(parts[-1]), published=True))
                else:
                    ports.append(PortMapping(container_port=int(parts[0]), published=False))

            services.append(ServiceNode(
                id=svc_id,
                name=svc_name,
                image=svc_def.get("image"),
                networks=svc_nets,
                published_ports=ports,
                depends_on=svc_def.get("depends_on", [])
            ))

        # 3. Build Edges (Relationships)
        for svc in services:
            # Dependency Edges
            for dep in svc.depends_on:
                edges.append(RelationshipEdge(
                    id=f"edge_dep_{svc.name}_{dep}",
                    source=svc.id,
                    target=f"svc_{dep}",
                    relationship="depends_on",
                    label="depends on"
                ))
                
            # Shared Network Edges
            for other_svc in services:
                if svc.id == other_svc.id:
                    continue
                shared = set(svc.networks).intersection(set(other_svc.networks))
                if shared:
                    edges.append(RelationshipEdge(
                        id=f"edge_net_{svc.name}_{other_svc.name}",
                        source=svc.id,
                        target=other_svc.id,
                        relationship="shares_network",
                        label="shares network",
                        metadata={"networks": list(shared)}
                    ))

        return TopologyGraph(
            project_id=project_id,
            version="baseline",
            services=services,
            networks=networks,
            edges=edges,
            warnings=parsed_data.get("warnings", [])
        )