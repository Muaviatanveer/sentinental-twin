# 🛡️ NeuroSyn Sentinel Twin — Security & Policy Architecture

> Maintained by **Sana Mahmood** ([@sanakhang2006-cyber](https://github.com/sanakhang2006-cyber))  
> Component: Security Policy Synthesis, Attack Surface Reduction, and Deterministic Threat Probing

---

## 1. Threat Model & Network Perimeter

Microservice applications running on Docker Compose typically execute on flat, default bridge networks. Under this topology:
- Every container can reach every other container on any open TCP/UDP port.
- Lateral movement is uninhibited if an internet-facing frontend service is compromised.
- Sensitive databases, caches, and internal microservices have zero network boundary protection.

Sentinel Twin addresses this by enforcing **Least-Privilege Network Segmentation**:
1. **Tier 1 (Public Edge)**: Frontend web containers only exposed via reverse proxy.
2. **Tier 2 (Application Layer)**: Internal FastAPI/Node.js application backends communicating exclusively with specific downstream services.
3. **Tier 3 (Data Layer)**: PostgreSQL, Redis, and internal message queues placed on isolated backend bridge networks with no direct reachability from Tier 1.

---

## 2. Policy Synthesis Pipeline

When a Docker Compose configuration is parsed:
1. **Multi-Graph Extraction**: `engine/graph_engine` produces a NetworkX MultiDiGraph $\mathcal{G}_0$.
2. **Attack Surface Audit**: Insecure bindings (`0.0.0.0:port`) and unsegmented shared networks are flagged.
3. **Gemma 4 Thinking Mode**: Synthesizes counterfactual network definitions (`frontend_net`, `backend_net`) and assigns each service strictly to its authorized networks.
4. **Counterfactual Reachability ($\Delta\mathcal{G}$)**: Computes reachability matrix difference $\mathcal{R}_1 - \mathcal{R}_0$ to guarantee that unauthorized lateral paths are eliminated without breaking required application connectivity.

---

## 3. Automated Verification via Live TCP Probes

Unlike static analysis tools, Sentinel Twin validates policies in **live, disposable Docker sandboxes**:
- Each policy rule is mapped to a concrete connectivity test case (`source`, `target`, `port`, `expected: ALLOW|DENY`).
- Probes are executed via `nc -zv` inside running container namespaces.
- Results are cryptographically signed with SHA-256 evidence digests.
