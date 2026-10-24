import networkx as nx
from apps.api.app.schemas.contracts import TopologyGraph

class GraphAnalyzer:
    @staticmethod
    def analyze_reachability(topology: TopologyGraph) -> TopologyGraph:
        """
        Calculates the reachability matrix based purely on shared Docker networks.
        """
        G = nx.DiGraph()
        
        # Add Nodes
        for svc in topology.services:
            G.add_node(svc.id, type="service", name=svc.name)
            
        # Add Network Edges (treating shared networks as bi-directional potential paths)
        for edge in topology.edges:
            if edge.relationship == "shares_network":
                G.add_edge(edge.source, edge.target, networks=edge.metadata.get("networks", []))
                
        # Calculate Reachability Matrix
        matrix: dict[str, dict[str, str]] = {}
        
        for source in topology.services:
            matrix[source.name] = {}
            for target in topology.services:
                if source.id == target.id:
                    continue
                
                # In Docker Compose bridge networks, if an edge exists, they can route to each other.
                if G.has_edge(source.id, target.id):
                    matrix[source.name][target.name] = "potentially_reachable"
                else:
                    matrix[source.name][target.name] = "blocked"
                    
        topology.reachability_matrix = matrix
        return topology