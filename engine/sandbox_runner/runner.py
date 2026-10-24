import copy
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
import yaml
from apps.api.app.core.config import settings


class SandboxRunner:
    @classmethod
    def execute_test_plan(
        cls,
        experiment_id: str,
        candidate_yaml: str,
        test_plan: list[dict[str, Any]],
    ) -> dict[str, Any]:
        start_time = time.monotonic()
        namespace = f"sentinel_{experiment_id.lower()}"
        temp_dir = Path(tempfile.mkdtemp(prefix=f"{namespace}_"))
        compose_file = temp_dir / "compose.yaml"

        # Sanitize candidate YAML for safe, port-collision-free isolated execution
        sanitized_yaml = cls._sanitize_for_sandbox(candidate_yaml)
        compose_file.write_text(sanitized_yaml, encoding="utf-8")

        results: list[dict[str, Any]] = []
        runner_logs: list[str] = []

        try:
            # 1. Verify Docker CLI / daemon availability
            up_cmd = [
                "docker",
                "compose",
                "-p",
                namespace,
                "-f",
                str(compose_file),
                "up",
                "-d",
            ]
            runner_logs.append(f"$ {' '.join(up_cmd)}")
            up_proc = subprocess.run(
                up_cmd,
                capture_output=True,
                text=True,
                timeout=settings.SANDBOX_TIMEOUT_SECONDS,
            )
            runner_logs.append(up_proc.stdout + up_proc.stderr)

            if up_proc.returncode != 0:
                raise RuntimeError(
                    f"Docker Compose failed to start sandbox: {up_proc.stderr.strip()}"
                )

            # Give lightweight listeners 1.5s to bind sockets inside containers
            time.sleep(1.5)

            # 2. Execute each real TCP connectivity probe inside the source container
            for item in test_plan:
                src = item["source"]
                dst = item["destination"]
                port = item["target_port"]
                expected = item["expected"]
                predicted = item["predicted"]

                probe_cmd = [
                    "docker",
                    "compose",
                    "-p",
                    namespace,
                    "-f",
                    str(compose_file),
                    "exec",
                    "-T",
                    src,
                    "nc",
                    "-zv",
                    "-w",
                    "2",
                    dst,
                    str(port),
                ]
                t0 = time.monotonic()
                try:
                    probe_proc = subprocess.run(
                        probe_cmd,
                        capture_output=True,
                        text=True,
                        timeout=6,
                    )
                    exit_code = probe_proc.returncode
                    raw_out = (probe_proc.stdout + "\n" + probe_proc.stderr).strip()
                except subprocess.TimeoutExpired:
                    exit_code = 124
                    raw_out = f"Connection timed out after 6s probing {dst}:{port} from {src}"

                elapsed_ms = int((time.monotonic() - t0) * 1000)

                # Exit code 0 means TCP connection succeeded (reachable)
                # Non-zero exit code (1 or 124) means connection refused / unreachable / timed out (blocked)
                actual_outcome = "reachable" if exit_code == 0 else "blocked"
                actual_action = "allow" if actual_outcome == "reachable" else "deny"

                observed_grade = "pass" if actual_action == expected else "fail"
                discrepancy = actual_action != predicted

                log_line = (
                    f"[Probe {src} -> {dst}:{port}] cmd='nc -zv -w 2 {dst} {port}' "
                    f"exit_code={exit_code} ({elapsed_ms}ms) outcome={actual_outcome}\n{raw_out}"
                ).strip()
                runner_logs.append(log_line)

                results.append(
                    {
                        "source": src,
                        "destination": dst,
                        "target_port": port,
                        "expected": expected,
                        "predicted": predicted,
                        "observed": observed_grade,
                        "actual_outcome": actual_outcome,
                        "discrepancy": discrepancy,
                        "exit_code": exit_code,
                        "output_log": log_line,
                    }
                )

        finally:
            # 3. Guaranteed teardown of containers, volumes, and networks
            down_cmd = [
                "docker",
                "compose",
                "-p",
                namespace,
                "-f",
                str(compose_file),
                "down",
                "-v",
                "--remove-orphans",
            ]
            try:
                down_proc = subprocess.run(
                    down_cmd, capture_output=True, text=True, timeout=20
                )
                runner_logs.append(f"$ {' '.join(down_cmd)}\n{down_proc.stdout}{down_proc.stderr}")
            except Exception as teardown_exc:
                runner_logs.append(f"Teardown warning: {teardown_exc}")

            shutil.rmtree(temp_dir, ignore_errors=True)

        duration_ms = int((time.monotonic() - start_time) * 1000)
        return {
            "duration_ms": duration_ms,
            "results": results,
            "runner_log": "\n".join(runner_logs),
            "sanitized_yaml": sanitized_yaml,
        }

    @staticmethod
    def _sanitize_for_sandbox(candidate_yaml: str) -> str:
        """
        Enforces Section 11 mandatory security safeguards:
        - Strips host port bindings so disposable twins never clash with host ports (e.g., 3000, 8000).
        - Strips privileged mode, host volumes, and host network_mode.
        """
        doc = copy.deepcopy(yaml.safe_load(candidate_yaml))
        doc.pop("name", None)

        for _svc_name, svc_def in doc.get("services", {}).items():
            # Convert host-published ports to internal expose so containers still listen
            if "ports" in svc_def:
                exposed = svc_def.get("expose", [])
                for p in svc_def.pop("ports", []):
                    container_port = str(p).split(":")[-1]
                    if container_port not in exposed:
                        exposed.append(container_port)
                svc_def["expose"] = exposed

            svc_def.pop("privileged", None)
            svc_def.pop("volumes", None)
            if svc_def.get("network_mode") == "host":
                svc_def.pop("network_mode", None)

        return yaml.safe_dump(doc, sort_keys=False)
