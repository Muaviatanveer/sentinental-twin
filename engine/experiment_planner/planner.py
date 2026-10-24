import re
from typing import Any
from apps.api.app.schemas.contracts import PolicyRequirement, TopologyGraph


class ExperimentPlanner:
    @staticmethod
    def build_test_plan(
        requirements: list[PolicyRequirement],
        candidate_topology: TopologyGraph,
        raw_candidate_yaml_dict: dict[str, Any],
    ) -> list[dict[str, Any]]:
        services_raw = raw_candidate_yaml_dict.get("services", {})
        plan: list[dict[str, Any]] = []

        for req in requirements:
            target_port = ExperimentPlanner._infer_service_port(
                req.destination, services_raw.get(req.destination, {})
            )
            c_reach = candidate_topology.reachability_matrix.get(req.source, {}).get(
                req.destination, "blocked"
            )
            predicted = "allow" if c_reach == "potentially_reachable" else "deny"

            plan.append(
                {
                    "source": req.source,
                    "destination": req.destination,
                    "target_port": target_port,
                    "expected": req.expected,
                    "predicted": predicted,
                }
            )
        return plan

    @staticmethod
    def _infer_service_port(service_name: str, svc_def: dict[str, Any]) -> int:
        # 1. Check ports list
        ports = svc_def.get("ports", [])
        if ports:
            first = str(ports[0]).split(":")[-1].split("/")[0]
            if first.isdigit():
                return int(first)

        # 2. Check expose list
        expose = svc_def.get("expose", [])
        if expose:
            first = str(expose[0]).split("/")[0]
            if first.isdigit():
                return int(first)

        # 3. Check command string for -p <port>
        cmd = str(svc_def.get("command", ""))
        match = re.search(r"-p\s+(\d+)", cmd)
        if match:
            return int(match.group(1))

        # 4. Sensible defaults by common tier name
        defaults = {"frontend": 3000, "api": 8000, "database": 5432, "redis": 6379}
        return defaults.get(service_name.lower(), 80)
