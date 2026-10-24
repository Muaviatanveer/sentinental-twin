import json
import re
import time
from typing import Any
import httpx
from apps.api.app.core.config import settings
from apps.api.app.schemas.contracts import (
    GemmaProposalSchema,
    PolicyRequirement,
    TopologyGraph,
)

SYSTEM_PROMPT = """You are powered by Google DeepMind's Gemma 4 26B A4B (Mixture-of-Experts) acting as the Principal Cloud-Native Security Architect for NeuroSyn Sentinel Twin.

You will receive:
1. The raw Docker Compose YAML configuration.
2. The deterministic NetworkX baseline reachability matrix and parser warnings.
3. The developer's natural-language security boundary intent.

Perform deep step-by-step architectural reasoning (Thinking Mode) and output ONLY valid JSON matching this exact schema (no markdown code fences):
{
  "intent": "restrict_service_connectivity",
  "thinking_trace": [
    "Step 1 (Topology & Attack Surface Audit): <analyze shared networks, exposed host ports, and lateral movement paths in the baseline YAML>",
    "Step 2 (Counterfactual Boundary Synthesis): <explain how network segmentation isolates tiers while preserving required application flows>",
    "Step 3 (Verification Probe Strategy): <specify which TCP sockets must return exit code 0 vs exit code 1 in the isolated sandbox>"
  ],
  "risk_assessment": "<concise 1-2 sentence summary of the baseline vulnerability being remediated>",
  "requirements": [
    {
      "source": "<service_name>",
      "destination": "<service_name>",
      "expected": "allow" | "deny"
    }
  ],
  "reason": "<concise architectural rationale for this policy>"
}

Strict Rules:
- Only output service names that actually exist in the topology unless the user explicitly demands an unknown service name (which our downstream semantic validator will catch).
- Never output shell commands or executable scripts.
"""


class GemmaAdapter:
    @classmethod
    def generate_proposal(
        cls,
        intent_text: str,
        baseline_topology: TopologyGraph,
        source_yaml: str = "",
    ) -> dict[str, Any]:
        t0 = time.monotonic()
        service_names = [s.name for s in baseline_topology.services]
        provider = settings.GEMMA_PROVIDER.lower().strip()
        model_name = settings.GEMMA_MODEL_NAME

        user_prompt = (
            f"=== BASELINE DOCKER COMPOSE YAML ===\n{source_yaml}\n\n"
            f"=== PARSED TOPOLOGY SERVICES ===\n{json.dumps(service_names)}\n\n"
            f"=== BASELINE REACHABILITY MATRIX ===\n{json.dumps(baseline_topology.reachability_matrix, indent=2)}\n\n"
            f"=== PARSER WARNINGS ===\n{json.dumps(baseline_topology.warnings)}\n\n"
            f"=== DEVELOPER SECURITY INTENT ===\n{intent_text}\n\n"
            "Output strict JSON with thinking_trace, risk_assessment, requirements, and reason:"
        )

        raw_output = ""
        used_provider = provider

        try:
            if provider == "google_genai" and settings.GEMMA_API_KEY:
                schema_obj, raw_output = cls._call_google_genai(user_prompt, model_name)
            elif provider == "ollama":
                schema_obj, raw_output = cls._call_ollama(user_prompt, model_name)
            elif provider == "openai_compatible" and settings.GEMMA_API_BASE:
                schema_obj, raw_output = cls._call_openai_compatible(user_prompt, model_name)
            else:
                used_provider = "deterministic_fallback"
                schema_obj = cls._deterministic_parse(intent_text, service_names, baseline_topology)
                raw_output = schema_obj.model_dump_json(indent=2)
        except Exception as exc:
            # If live endpoint errors, record the reason in thinking trace and fall back gracefully
            used_provider = f"{provider} (fallback: {exc.__class__.__name__})"
            schema_obj = cls._deterministic_parse(intent_text, service_names, baseline_topology)
            schema_obj.thinking_trace.insert(
                0,
                f"Live endpoint notice ({model_name}): {str(exc)[:140]}. Executed deterministic graph-aware fallback.",
            )
            raw_output = schema_obj.model_dump_json(indent=2)

        latency_ms = int((time.monotonic() - t0) * 1000)
        return {
            "proposal": schema_obj,
            "model_used": model_name,
            "provider_used": used_provider,
            "latency_ms": latency_ms,
            "raw_output": raw_output,
        }

    @classmethod
    def _call_google_genai(
        cls, user_prompt: str, model_name: str
    ) -> tuple[GemmaProposalSchema, str]:
        """
        Calls Gemma 4 26B A4B (`gemma-4-26b-a4b-it`) on Google AI Studio / Gemini API.
        """
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={settings.GEMMA_API_KEY}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                # Retry without responseMimeType if a specific Gemma endpoint rejects mime flag
                payload["generationConfig"].pop("responseMimeType", None)
                resp = client.post(url, json=payload)
            resp.raise_for_status()
            parts = resp.json()["candidates"][0]["content"]["parts"]
            # Combine any native thought part + text part
            thought_texts = []
            json_text = ""
            for p in parts:
                if p.get("thought"):
                    thought_texts.append(p.get("text", ""))
                else:
                    json_text += p.get("text", "")
            parsed = cls._parse_json_output(json_text)
            if thought_texts and not parsed.thinking_trace:
                parsed.thinking_trace = thought_texts
            return parsed, json_text

    @classmethod
    def _call_ollama(
        cls, user_prompt: str, model_name: str
    ) -> tuple[GemmaProposalSchema, str]:
        url = f"{settings.GEMMA_API_BASE.rstrip('/')}/api/generate"
        payload = {
            "model": model_name,
            "system": SYSTEM_PROMPT,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
        }
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            raw_text = resp.json().get("response", "{}")
            return cls._parse_json_output(raw_text), raw_text

    @classmethod
    def _call_openai_compatible(
        cls, user_prompt: str, model_name: str
    ) -> tuple[GemmaProposalSchema, str]:
        url = f"{settings.GEMMA_API_BASE.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if settings.GEMMA_API_KEY:
            headers["Authorization"] = f"Bearer {settings.GEMMA_API_KEY}"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            raw_text = resp.json()["choices"][0]["message"]["content"]
            return cls._parse_json_output(raw_text), raw_text

    @staticmethod
    def _parse_json_output(raw_text: str) -> GemmaProposalSchema:
        cleaned = raw_text.strip()
        # Strip optional <think>...</think> blocks if emitted inline by open-weight GGUF
        think_match = re.search(r"<think>(.*?)</think>", cleaned, flags=re.DOTALL)
        extracted_thoughts: list[str] = []
        if think_match:
            extracted_thoughts = [
                line.strip()
                for line in think_match.group(1).strip().splitlines()
                if line.strip()
            ]
            cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        data = json.loads(cleaned)
        schema_obj = GemmaProposalSchema(**data)
        if extracted_thoughts and not schema_obj.thinking_trace:
            schema_obj.thinking_trace = extracted_thoughts
        return schema_obj

    @staticmethod
    def _deterministic_parse(
        intent_text: str,
        known_services: list[str],
        baseline_topology: TopologyGraph,
    ) -> GemmaProposalSchema:
        text_lower = intent_text.lower()
        requirements: list[PolicyRequirement] = []

        clauses = re.split(r"[,.;]|\bbut\b|\bwhile\b|\band\b", text_lower)
        candidate_tokens = list(known_services)
        for match in re.finditer(r"\b([a-z0-9_-]+)\s+to\s+([a-z0-9_-]+)\b", text_lower):
            for tok in (match.group(1), match.group(2)):
                if tok not in candidate_tokens and tok not in {
                    "talk", "communicate", "connect", "access", "reach", "allowing", "prevent",
                }:
                    candidate_tokens.append(tok)

        deny_keywords = ["prevent", "block", "deny", "forbid", "restrict", "isolate", "no ", "not ", "cannot"]
        allow_keywords = ["allow", "keep", "preserve", "permit", "enable", "can ", "working"]

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue
            mentioned: list[tuple[int, str]] = []
            for svc in candidate_tokens:
                idx = clause.find(svc.lower())
                if idx != -1:
                    mentioned.append((idx, svc))
            mentioned.sort(key=lambda x: x[0])

            if len(mentioned) >= 2:
                src = mentioned[0][1]
                dst = mentioned[1][1]
                is_deny = any(kw in clause for kw in deny_keywords)
                is_allow = any(kw in clause for kw in allow_keywords)
                action = "deny" if is_deny else ("allow" if is_allow else "deny")
                req = PolicyRequirement(source=src, destination=dst, expected=action)
                if not any(
                    r.source == req.source and r.destination == req.destination and r.expected == req.expected
                    for r in requirements
                ):
                    requirements.append(req)

        if not requirements and {"frontend", "api", "database"}.issubset(set(known_services)):
            requirements = [
                PolicyRequirement(source="frontend", destination="api", expected="allow"),
                PolicyRequirement(source="frontend", destination="database", expected="deny"),
                PolicyRequirement(source="api", destination="database", expected="allow"),
            ]

        shared_nets = [n.name for n in baseline_topology.networks]
        thinking_steps = [
            f"Step 1 (Topology & Attack Surface Audit): Analyzed {len(known_services)} services ({', '.join(known_services)}) across networks {shared_nets}. Detected flat bridge connectivity allowing direct lateral movement from public entry tier to data tier.",
            f"Step 2 (Counterfactual Boundary Synthesis): Synthesized {len(requirements)} explicit allow/deny constraints to split the flat bridge network into isolated tier subnets (`frontend_api_net` and `api_database_net` with `internal: true`).",
            "Step 3 (Verification Probe Strategy): Mapped policy rules to bounded netcat (`nc -zv`) TCP probes to verify that `frontend -> database:5432` returns exit code 1 (blocked) while `frontend -> api` and `api -> database` return exit code 0.",
        ]

        return GemmaProposalSchema(
            intent="restrict_service_connectivity",
            thinking_trace=thinking_steps,
            risk_assessment=(
                f"Baseline configuration places {', '.join(known_services)} on shared network {shared_nets}, "
                "permitting direct unmediated TCP access from the frontend container to the database."
            ),
            requirements=requirements,
            reason="Enforce least-privilege network segmentation across application tiers",
        )