import copy
import difflib
import yaml
from typing import Any
from apps.api.app.schemas.contracts import (
    PathImpact,
    PolicyRequirement,
    RelationshipEdge,
    TopologyGraph,
)
from engine.compose_parser.parser import ComposeParser
from engine.twin_builder.builder import TwinBuilder
from engine.graph_engine.analyzer import GraphAnalyzer


class PolicySynthesizer:
    @staticmethod
    def validate_requirements(
        requirements: list[PolicyRequirement], baseline: TopologyGraph
    ) -> list[str]:
        errors: list[str] = []
        known_services = {s.name for s in baseline.services}

        if not requirements:
            errors.append("Proposal contains no connectivity requirements.")
            return errors

        seen_pairs: dict[tuple[str, str], str] = {}

        for req in requirements:
            if req.source not in known_services:
                errors.append(f"Unknown source service '{req.source}'. Known services: {sorted(known_services)}")
            if req.destination not in known_services:
                errors.append(f"Unknown destination service '{req.destination}'. Known services: {sorted(known_services)}")
            if req.source == req.destination:
                errors.append(f"Service '{req.source}' cannot define a connectivity policy to itself.")

            # Check direct or symmetric conflicts (Docker bridge networks are bidirectional at L3/L4)
            pair_key = tuple(sorted([req.source, req.destination]))
            if pair_key in seen_pairs and seen_pairs[pair_key] != req.expected:
                errors.append(
                    f"Conflicting requirements between '{req.source}' and '{req.destination}': "
                    f"cannot simultaneously '{seen_pairs[pair_key]}' and '{req.expected}' shared bridge network access."
                )
            seen_pairs[pair_key] = req.expected

        return errors

    @classmethod
    def simulate(
        cls,
        project_id: str,
        proposal_id: str,
        baseline_yaml: str,
        baseline_topology: TopologyGraph,
        requirements: list[PolicyRequirement],
    ) -> dict[str, Any]:
        # 1. Synthesize candidate Compose YAML
        candidate_yaml = cls._synthesize_candidate_yaml(
            baseline_yaml, baseline_topology, requirements
        )

        # 2. Parse & build Candidate Topology Graph (G1)
        parsed_candidate = ComposeParser.parse(candidate_yaml)
        candidate_topology = TwinBuilder.build_topology(project_id, parsed_candidate)
        candidate_topology.version = f"candidate:{proposal_id}"
        candidate_topology = GraphAnalyzer.analyze_reachability(candidate_topology)

        # 3. Compute Pairwise Reachability & Path Impacts (Delta G = G1 - G0)
        baseline_flat: dict[str, str] = {}
        candidate_flat: dict[str, str] = {}
        impacts: list[PathImpact] = []

        # Map explicit rules for quick lookup
        rule_map: dict[tuple[str, str], PolicyRequirement] = {}
        for r in requirements:
            rule_map[(r.source, r.destination)] = r

        services = [s.name for s in baseline_topology.services]
        for src in services:
            for dst in services:
                if src == dst:
                    continue
                key = f"{src}_to_{dst}"
                b_state = baseline_topology.reachability_matrix.get(src, {}).get(dst, "blocked")
                c_state_raw = candidate_topology.reachability_matrix.get(src, {}).get(dst, "blocked")

                explicit_rule = rule_map.get((src, dst)) or rule_map.get((dst, src))
                if c_state_raw == "blocked" and b_state == "potentially_reachable":
                    c_state = "blocked_by_candidate_policy"
                    change_type = "newly_blocked"
                elif c_state_raw == "potentially_reachable" and b_state == "blocked":
                    c_state = "potentially_reachable"
                    change_type = "newly_permitted"
                else:
                    c_state = c_state_raw
                    change_type = "unchanged"

                # Check if candidate violates an explicit requirement
                if explicit_rule:
                    if explicit_rule.expected == "deny" and c_state_raw == "potentially_reachable":
                        change_type = "conflicting"
                    elif explicit_rule.expected == "allow" and c_state_raw == "blocked":
                        change_type = "conflicting"

                baseline_flat[key] = b_state
                candidate_flat[key] = c_state

                # Include in impact list if it changed OR was explicitly requested
                if change_type != "unchanged" or (src, dst) in rule_map:
                    rule_desc = (
                        f"Policy rule: {explicit_rule.source} -> {explicit_rule.destination} ({explicit_rule.expected.upper()})"
                        if explicit_rule
                        else "Transitive network segmentation effect"
                    )
                    impacts.append(
                        PathImpact(
                            source=src,
                            destination=dst,
                            baseline_state=b_state,
                            candidate_state=c_state,
                            change_type=change_type,
                            rule_applied=rule_desc,
                            assumptions=[
                                "Docker bridge network isolation blocks cross-network container routing",
                                "Shared Docker network membership grants L3/L4 reachability",
                            ],
                        )
                    )

        # 4. Annotate visual diff edges on Candidate Topology so the UI can highlight blocked paths
        candidate_edge_pairs = {
            (e.source, e.target)
            for e in candidate_topology.edges
            if e.relationship == "shares_network"
        }
        baseline_edge_pairs = {
            (e.source, e.target)
            for e in baseline_topology.edges
            if e.relationship == "shares_network"
        }

        for edge in candidate_topology.edges:
            if edge.relationship == "shares_network":
                if (edge.source, edge.target) not in baseline_edge_pairs:
                    edge.diff_status = "newly_permitted"
                else:
                    edge.diff_status = "unchanged"

        # Add ghost edges for newly blocked relationships so React Flow renders them in red
        for b_edge in baseline_topology.edges:
            if (
                b_edge.relationship == "shares_network"
                and (b_edge.source, b_edge.target) not in candidate_edge_pairs
            ):
                blocked_edge = RelationshipEdge(
                    id=f"blocked_{b_edge.source}_{b_edge.target}",
                    source=b_edge.source,
                    target=b_edge.target,
                    relationship="shares_network",
                    label="blocked by policy",
                    metadata={"networks": []},
                    diff_status="newly_blocked",
                )
                candidate_topology.edges.append(blocked_edge)

        # 5. Compute unified YAML diff
        yaml_diff = "\n".join(
            difflib.unified_diff(
                baseline_yaml.splitlines(),
                candidate_yaml.splitlines(),
                fromfile="compose.baseline.yaml",
                tofile="compose.candidate.yaml",
                lineterm="",
            )
        )

        return {
            "baseline_reachability": baseline_flat,
            "candidate_reachability": candidate_flat,
            "impacts": impacts,
            "candidate_topology": candidate_topology,
            "candidate_yaml": candidate_yaml,
            "yaml_diff": yaml_diff,
        }

    @staticmethod
    def _synthesize_candidate_yaml(
        baseline_yaml: str,
        baseline_topology: TopologyGraph,
        requirements: list[PolicyRequirement],
    ) -> str:
        raw_doc = copy.deepcopy(yaml.safe_load(baseline_yaml))
        services_dict: dict[str, Any] = raw_doc.get("services", {})

        denied_pairs: set[tuple[str, str]] = set()
        allowed_pairs: list[tuple[str, str]] = []

        for req in requirements:
            pair = (req.source, req.destination)
            rev_pair = (req.destination, req.source)
            if req.expected == "deny":
                denied_pairs.add(pair)
                denied_pairs.add(rev_pair)
            elif req.expected == "allow":
                if pair not in allowed_pairs and rev_pair not in allowed_pairs:
                    allowed_pairs.append(pair)

        # If any deny rule exists, segment the shared network into dedicated tier networks
        if denied_pairs:
            # Preserve existing baseline connections that were NOT denied if no explicit allow list was given
            if not allowed_pairs:
                all_svcs = [s.name for s in baseline_topology.services]
                for i, s1 in enumerate(all_svcs):
                    for s2 in all_svcs[i + 1 :]:
                        if (s1, s2) not in denied_pairs:
                            allowed_pairs.append((s1, s2))

            new_networks: dict[str, Any] = {}
            service_net_map: dict[str, list[str]] = {name: [] for name in services_dict}

            # Identify services with published host ports (entry tier)
            published_services = {
                s.name for s in baseline_topology.services if any(p.published for p in s.published_ports)
            }

            for s1, s2 in allowed_pairs:
                if (s1, s2) in denied_pairs:
                    continue
                net_name = f"{s1}_{s2}_net"
                # Mark backend/data tier networks as internal if neither service publishes host ports
                is_internal = (s1 not in published_services) and (s2 not in published_services)
                net_cfg: dict[str, Any] = {"driver": "bridge"}
                if is_internal:
                    net_cfg["internal"] = True
                new_networks[net_name] = net_cfg

                if s1 in service_net_map and net_name not in service_net_map[s1]:
                    service_net_map[s1].append(net_name)
                if s2 in service_net_map and net_name not in service_net_map[s2]:
                    service_net_map[s2].append(net_name)

            # Ensure any completely isolated service still gets its own isolated network
            for svc_name, nets in service_net_map.items():
                if not nets:
                    iso_net = f"{svc_name}_isolated_net"
                    new_networks[iso_net] = {"driver": "bridge", "internal": True}
                    service_net_map[svc_name].append(iso_net)

            for svc_name, svc_def in services_dict.items():
                svc_def["networks"] = service_net_map.get(svc_name, [])

            raw_doc["networks"] = new_networks

        return yaml.safe_dump(raw_doc, sort_keys=False)