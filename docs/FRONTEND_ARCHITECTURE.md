# ⚡ NeuroSyn Sentinel Twin — Frontend & UX Architecture

> Maintained by **Maryam Arif** ([@MaryamArif17](https://github.com/MaryamArif17))  
> Component: Next.js 14 Web Workspace, Interactive Graph Visualization, and Evidence Diffing

---

## 1. Design System & User Experience

Sentinel Twin's web interface is engineered for real-time observability and interactive security analysis:
- **Framework**: Next.js 14 App Router with TypeScript and Tailwind CSS.
- **Aesthetic**: Cyberpunk obsidian dark theme with high-contrast status accents (`#00D4FF` cyan, `#10B981` emerald, `#EF4444` crimson, `#A78BFA` violet).
- **Responsiveness**: Fluid layout with real-time feedback across policy generation, simulation, and sandbox execution phases.

---

## 2. Core Workspace Screens

1. **Dashboard Overview (`/`)**:
   - Live system health status, active sandbox counts, verification success rate.
   - Quick launch for standard hackathon demonstration fixtures.

2. **Project Detail & Topology Graph (`/projects/[id]`)**:
   - Interactive network topology rendering with node clustering and edge type filters (`shared_network`, `published_port`, `depends_on`).
   - Attack surface inspector with flagged security risks.

3. **Gemma 4 Policy Workspace (`/projects/[id]/proposals`)**:
   - Natural language counterfactual policy synthesis.
   - Live inference latency display and Gemma 4 Thinking Mode reasoning card.
   - Candidate policy editor with interactive toggle controls.

4. **Sandbox Execution Workspace (`/projects/[id]/experiments/[expId]`)**:
   - Live terminal log streaming for sandbox provisioning and probe execution.
   - Step-by-step progress tracking for disposable Docker test runners.

5. **Evidence Report Viewer (`/projects/[id]/reports/[reportId]`)**:
   - Side-by-side YAML diff viewer highlighting network segmentation modifications.
   - Cryptographic SHA-256 evidence digests and downloadable Markdown/JSON verification certificates.
