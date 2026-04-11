# Design Principles for Agent-Native CLI Tools (2026)

To be effectively utilized by AI agents (e.g., Gemini, Claude Code, OpenDevin), CLI tools must move beyond human-centric "pretty" output and prioritize parseability, safety, and token efficiency.

### Implementation Strategy

| Feature | Retrofit Priority | Future Requirement | Why? |
| :--- | :--- | :--- | :--- |
| Output Format | Add `--json` flag | JSON-first architecture | Prevents parsing hallucinations. |
| Interactivity | Add `--yes` to all | Zero-interactivity mode | Interactive prompts kill agent loops. |
| Safety | Add `--dry-run` | Plan-then-Execute | Avoids irreversible agent errors. |
| Discovery | Better `--help` text | MCP / `--schema` | Machine-to-machine interface discovery. |
| Token Usage | N/A | `--fields` filtering | Keeps agent context windows lean. |

### UX Patterns

| Pattern | Human UX | Agentic UX | Purpose |
| :--- | :--- | :--- | :--- |
| Discovery | man pages | `--schema` / MCP | Machine-readable capabilities |
| Safety | "Are you sure?" | `--dry-run` / `--yes` | Non-blocking verification |
| Efficiency | Paged text | `--fields` / JSON | Token conservation |
| Workflow | Human intuition | `next_actions` array | Reducing hallucination |
| Governance | Manual checks | Plan-Then-Execute | Human-in-the-loop (HITL) |

### Design Comparison

| Feature | Human-Centric Design | Agentic-Centric Design |
| :--- | :--- | :--- |
| Output | Beautiful ASCII tables | Minified JSON |
| Feedback | "Done! 🚀" in green text | Exit Code 0 |
| Errors | Friendly prose | Error Code + JSON `error_type` |
| UX | Interactive prompts | `--yes` flags |
| Discovery | Massive PDF Manuals | Granular `--help` flags |

## 1. Machine-Interfacing Core

### Machine-Readable Output (JSON First)
Every command must support a `--json` or `--format json` flag.

**Reasoning**: LLMs are prone to hallucinating values when scraping data from ASCII tables. Structured JSON allows the agent to use exact keys, ensuring reliable data passing between steps.

### Deterministic Exit Codes
Strict adherence to Unix exit codes (0 for success, non-zero for specific error types).

**Reasoning**: Exit codes are the primary "branching" signal for agents. A 0 means "proceed," while specific non-zero codes (e.g., 401 for Auth, 404 for Missing) help the agent choose a self-healing strategy.

### Clean Stream Separation (STDOUT vs. STDERR)
Data belongs in stdout; logs, progress bars, and warnings belong in stderr.

**Reasoning**: Agents often pipe output to other utilities. Mixing "Loading..." animations into the data stream corrupts the payload and breaks the agent's parsing logic.

### Zero-Interactivity
Ensure all prompts can be bypassed with `--yes` or `--force` flags.

**Reasoning**: Interactive [y/n] prompts are "dead ends" for autonomous agents. If a tool hangs waiting for input, the agentic loop times out and fails.

## 2. Advanced Agentic Patterns

### Capability Introspection (MCP Support)
Provide machine-readable definitions via flags like `--schema` or `--describe`.

**Reasoning**: This makes the tool compatible with the Model Context Protocol (MCP). It allows the agent to discover capabilities and argument types programmatically rather than "guessing" flags.

### Predictive "Next Actions"
Include a `next_actions` array in JSON responses containing valid command templates for follow-up steps.

**Reasoning**: This acts as HATEOAS for the terminal. It provides a "menu" of valid actions, preventing the agent from hallucinating invalid flags or sub-commands.

### Plan-Then-Execute
For complex or high-risk tasks, output a structured "Plan" first for approval before execution.

**Reasoning**: This facilitates Human-in-the-Loop (HITL) governance. The agent proposes a sequence of changes, allowing a human or a reviewer agent to verify the logic before the CLI "commits" the action.

## 3. Efficiency & Safety

### Context Window Protection
Use a `--fields` flag to let agents request only the data they need.

**Reasoning**: Ingesting large JSON payloads wastes tokens and risks "distracting" the agent. Field selection keeps the context window lean and focused on high-signal data.

### Dry Run & Validation
Support a `--dry-run` flag for every mutation (Create/Update/Delete).

**Reasoning**: This allows the agent to verify its intent against the tool's validation logic without making irreversible changes. It’s a mandatory safety check for autonomous workflows.

### Idempotency by Design
Ensure running the same command twice does not result in an error or unintended duplicates.

**Reasoning**: Agents frequently retry commands after network hiccups. Idempotent tools allow for safe retries without corrupting the environment.

### Granular Documentation
Provide concise, per-command `--help` text.

**Reasoning**: Agents use "progressive disclosure"—running help commands to learn on-the-fly rather than reading a massive external manual. This saves tokens and keeps the focus narrow.
