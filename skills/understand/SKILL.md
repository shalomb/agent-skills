---
name: understand
description: >-
  Generate interactive, navigable repository, topic, PR, and diff reports and
  glossaries stored in shadow cache and served over local Parallels and Tailnet
  HTTP servers. Use when onboarding to an unfamiliar codebase, tracing a topic,
  reviewing a PR, or inspecting diffs with deep visual structure, C4 views,
  Cytoscape graph navigation, and contextual glossaries. Triggers: /understand,
  /understand <topic>, /understand-pr <pr>, /understand-diff <ref>, 'understand
  repository', 'visualize repo', 'codebase map'.
---

# Understand

Autonomous repository exploration and visual architectural intelligence. `/understand` produces rich, interactive, offline-capable visual reports, line-anchored source views, Cytoscape graph views, and contextual glossaries with zero repository pollution.

Reports live in a user shadow cache outside the repository and are served securely over local Parallels and Tailnet HTTP endpoints.

---

## Core Tenets & Anti-Goals

Every `/understand` run strictly adheres to four operational guardrails:

| Guardrail | Operational Rule | Architectural Rationale |
|---|---|---|
| **Never mutate repository** | Zero writes to repository files, git branches, or git history. Uncommitted changes remain intact. | Analysis must be safe to execute anywhere, anytime, on clean or dirty worktrees. |
| **Never write raw HTML** | Agents generate structured JSON and Markdown bundles; HTML is exclusively emitted by the deterministic, tested Python renderer. | Eliminates prompt token bloat, prevents layout hallucination, and ensures a unified design system ([ADR 0001](../../docs/adr/0001-bundle-and-fixed-renderer.md)). |
| **Never require network for viewing** | All report assets (CSS tokens, Cytoscape.js graph engine, vendored Mermaid fallback, inline SVG icons) work completely offline. | Reports remain fully readable in air-gapped environments, on airplanes, or during network outages. |
| **Never expose secrets or `$HOME`** | The report server allows only `/r/` (shadow cache) and `/src/` (`~/projects`). Dotfiles (`.env`, `.git`) and escaping symlinks are rejected with 404. | Protects developer credentials (`~/.ssh`, `~/.aws`, tokens) from local network exposure ([ADR 0002](../../docs/adr/0002-report-server-allow-list.md)). |

---

## The 4 Execution Phases

A report run executes deterministically through four sequential phases:

```
┌───────────┐      ┌──────────────┐      ┌──────────────┐      ┌────────────┐
│  1. Plan  │ ───> │ 2. Discover  │ ───> │ 3. Converge  │ ───> │ 4. Render  │
└───────────┘      └──────────────┘      └──────────────┘      └────────────┘
  Pre-scan           Read-only             Bundle synthesis      HTML + graph
  Calibrate tier     Delegates fan-out     Schema v1 contract    Serve & link
```

### Phase 1: Plan
- **Pre-scan**: Inspects file counts, directory hierarchy, primary languages, and content profiles (`code`, `docs`, or `mixed`).
- **Tier Calibration**:
  - *Small (<1,000 files)*: 3 read-only delegates split by architectural aspect (structure, dependencies, domain).
  - *Medium (<10,000 files)*: Aspects $\times$ areas, capped at 8 delegates.
  - *Large ($\ge$10,000 files)*: High-level areas only (depth 2), capped at 12 delegates.
- **Profile Adaptation**: Codebases with primarily documentation receive a document map and reading order rather than call graphs.
- **Focus Narrowing**: For topic, PR, or diff lenses, narrows scope to relevant subsystems before delegating.

### Phase 2: Discover
- **Read-Only Delegates**: Background delegates execute using `bg_delegate` with the `inspect` capability only.
- **Targeted Extraction**: Delegates map module boundaries, trace call graphs, isolate data contracts, and catalog bounded context terminology.
- **Lens Graph Focus**:
  - *Topic Lens*: Identifies semantic seed nodes, includes 1-hop neighbours, and dims peripheral nodes.
  - *PR Lens*: Queries PR metadata via `gh pr view`, builds a detached worktree in shadow storage, and catalogs changes.
  - *Diff Lens*: Computes `git merge-base(<ref>, HEAD)`, capturing working tree modifications while ignoring base-only drift.

### Phase 3: Converge
- **Bundle Synthesis**: Delegates merge findings into a structured bundle directory satisfying Schema Version 1:
  - `graph.json`: Nodes (`anchor_id`, `label`, `path`, `kind`, `summary`, `dimmed`) and edges (`source`, `target`, `kind`).
  - `sections/*.md`: Numbered narrative sections (e.g. `01-overview.md`, `02-architecture.md`).
  - `anchors.json`: Map of stable anchor IDs (`<path>` or `<path>::<symbol>`) to `{path, line}`.
  - `glossary.json`: Extracted bounded contexts, terminology, and collision metadata.
  - `glossary-draft.md`: Markdown proposal for a repository glossary.
- **Schema Validation**: Validates all JSON nodes and edge contracts before invoking the renderer.

### Phase 4: Render
- **Static Compilation**: The Python renderer (`understand_render`) compiles the bundle into `report.html`.
- **Source Views**: Generates syntax-highlighted source views under `src/<path>.html` with line-level anchor targets (`id="L<n>"`).
- **Diagram Processing**: Pre-renders Mermaid diagrams to inline SVG using `mmdc` and `chromium-headless-shell`; gracefully falls back to vendored in-page Mermaid if headless browser tooling is absent.
- **Index & Completion**: Updates global and per-repository indexes and emits a concise 5-line status message with dual HTTP report URLs.

---

## Command Surface & Lenses

`/understand` offers four primary lenses, invokable via slash commands or subcommands with shell auto-completion for `pr` and `diff`.

```bash
/understand                     # Full repository lens
/understand <topic>             # Topic lens (e.g. /understand auth)
/understand pr <number>         # PR lens (e.g. /understand pr 123)
/understand-pr <number>         # Alias for PR lens
/understand diff <ref>          # Diff lens (e.g. /understand diff main)
/understand-diff <ref>          # Alias for Diff lens
```

| Lens | Invocation | Target & Behavior | Git Required? |
|---|---|---|---|
| **Full** | `/understand` | Comprehensive architectural map of the entire repository or directory. | No |
| **Topic** | `/understand <topic>` | Focuses on a concept, subsystem, or feature flow (e.g. `billing retries`). Expands topic into seed terms, includes 1-hop neighbours, and dims outside nodes. | No |
| **PR** | `/understand pr <number>`<br>`/understand-pr <number>` | Reviews a GitHub pull request. Inspects PR metadata via `gh pr view`, provisions a temporary detached worktree in shadow storage at PR head, sets changed files as focus set, and tears down the worktree. Leaves current branch and uncommitted work untouched. | Yes |
| **Diff** | `/understand diff <ref>`<br>`/understand-diff <ref>` | Compares current working tree (including uncommitted edits) against `git merge-base(<ref>, HEAD)`. Focuses strictly on local branch delta, excluding changes committed to base branch after branching. | Yes |

---

## Shadow Directory Architecture

All generated artifacts, temporary worktrees, and cache indices are stored strictly outside the target repository under `XDG_CACHE_HOME`:

```
~/.cache/agent-skills/understand/
├── <repo-slug>/
│   ├── full/
│   │   ├── <commit>-<timestamp>/
│   │   │   ├── report.html         # Interactive visual report
│   │   │   ├── src/                # Line-anchored source views (L1, L2, ...)
│   │   │   ├── graph.json          # Cytoscape graph definition
│   │   │   ├── anchors.json        # Stable anchor index
│   │   │   ├── glossary.json       # Bounded context dictionary
│   │   │   ├── glossary-draft.md   # Proposed GLOSSARY.md patch
│   │   │   ├── run.json            # Run metadata and timestamp
│   │   │   └── render.log          # Diagram build diagnostics
│   │   └── latest -> <run-id>/     # Symlink to newest run of this lens
│   ├── topic-<topic-slug>/
│   ├── pr-<number>/
│   └── diff-<ref>/
└── wt/                             # Ephemeral detached worktrees for PR reviews
```

### Key Storage Conventions:
- **Repo Slug**: Matches the slug naming convention used by `todo-navigator` (derived from git root or resolved directory).
- **Run Identifier**: Formatted as `<commit-sha>-<utc-timestamp>` (or `<timestamp>` in non-git directories).
- **5-Run Retention Policy**: Each lens retains its 5 newest runs. Generating a sixth run automatically purges the oldest run for that specific lens without affecting runs of other lenses.
- **Stable Anchors**: Anchors derive from source paths and symbols (`path` or `path::symbol`), remaining deterministic across file reordering.

---

## Report Server & Local/Tailnet HTTP Delivery

Reports and source views are served over port `8787` by a lightweight, user-level nginx process (`systemd --user`) requiring zero administrator/sudo privileges ([ADR 0002](../../docs/adr/0002-report-server-allow-list.md), [ADR 0003](../../docs/adr/0003-report-server-tailnet-access.md)).

### Network Boundary & Fault Tolerance

```
Host Mac Browser ────────> [10.211.55.0/24]   ──┐
                                                 ├──> Report Server (:8787)
Tailnet Devices  ────────> [100.64.0.0/10]    ──┤    (systemd --user)
                           [fd7a:115c:a1e0::] ──┘
Other Networks   ────────> Access Denied (404)
```

- **Dual-Instance Architecture**:
  - `understand-report-server@parallels`: Listens on the VM's Parallels IP (`10.211.55.0/24`).
  - `understand-report-server@tailnet`: Listens on the VM's Tailnet addresses (`100.64.0.0/10`, `fd7a:115c:a1e0::/48`).
- **Resilience**: The Parallels instance serves the host Mac continuously even if Tailscale is disconnected or restarting.
- **Allowed Serve Roots**:
  - `/r/` $\rightarrow$ Shadow cache root (`~/.cache/agent-skills/`).
  - `/src/` $\rightarrow$ Projects directory (`~/projects`).
- **Security Hardening**:
  - Returns 404 for any path segment containing a dot (blocks `.env`, `.git`, `.ssh`, `.aws`).
  - Enforces `disable_symlinks on` to prevent directory traversal outside serve roots.
  - Never binds wildcard (`0.0.0.0`) or unapproved network interfaces.

### Completion Message Contract

On completion, `/understand` prints a concise summary of 5 lines or less:

```text
Report ready: agent-skills (full)
Parallels: http://10.211.55.3:8787/r/understand/agent-skills/full/c1a2b3-20261030T143000Z/
Tailnet:   http://100.99.83.53:8787/r/understand/agent-skills/full/c1a2b3-20261030T143000Z/
Summary:   Full overview of 142 files and 18 folders.
```

---

## Contextual Glossary & Collision Detection

Every report terminates with an architectural glossary (`sections/99-glossary.md`) designed to disambiguate domain terms.

### 1. Bounded Context Grouping
- Reads `GLOSSARY-MAP.md` if present in the repository root.
- If absent, automatically infers bounded contexts from top-level subsystems and directory boundaries (e.g. `src/billing` vs. `src/identity`).
- Groups domain terms under their respective contexts.

### 2. Polysemy & Term Collision Detection
- Analyzes terms across contexts to detect semantic collisions (terms with conflicting meanings in different subsystems).
- *Example*: `Account` meaning "payer of invoices" in `billing` vs. "login principal" in `identity`.
- Flags collisions prominently in the report, linking directly to each context-specific definition.

### 3. Non-Mutating Glossary Proposal
- Emits `glossary-draft.md` in the shadow run directory as a proposed `GLOSSARY.md` file.
- The user or agent can inspect, adapt, or apply the proposal to the repo manually.
- **The skill never writes `GLOSSARY.md` directly to the repository.**

---

## CLI & Tooling Reference

### Running a Report Programmatically

From Python or agent scripts:

```python
from understand_runs.runner import run_report

# Run full report
result = run_report(repo_path=".", lens="full")

# Run topic report
result = run_report(repo_path=".", lens="topic", target="authentication")

# Access URLs and summary
print(result.end_message)
```

### Running the Fixed Renderer Directly

```bash
cd skills/understand/scripts
python3 -m understand_render <bundle_dir> <out_dir> --source-root <repo_dir>
```

### Managing the Report Server

```bash
cd skills/understand/server

# Check generated nginx configuration
python3 -m report_server render --network parallels

# Dry-run service installation
./install.sh --dry-run --enable

# Enable and start user systemd units
./install.sh --enable
```
