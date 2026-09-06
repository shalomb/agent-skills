# Todo Navigator — CLI Reference

The `todo` CLI provides task backlog navigation, dependency management, and interactive editing with zero repository pollution.

## Global Options

- `--shadow`: Force operations against user cache (`~/.cache/agent-skills/todos/<repo_slug>/`). Default when no repo `TODO.md` is present.
- `-h`, `--help`: Display help and command usage.

---

## Subcommands

### 1. `list`
Prints concise task heading lines without dumping full markdown bodies.

```bash
todo list [query]
```

- **Without arguments:** Lists all tasks in active backlog.
- **With `query`:** Filters tasks using smart/partial matching (substring, stem, or token match).

**Output format:**
```text
[ ] [P1] [core-engine] Build Core Engine (WSJF: 2.0)
[ ] [P2] [editor-launch] Implement Editor (after: core-engine)
[x] [P0] [setup] Project Scaffolding
```

---

### 2. `add`
Creates a new task in `TODO.md` and automatically scaffolds a BDD task card in `tasks/<id>.md`.

```bash
todo add "<title>" [--id <id>] [--prio P0-P3] [--after <id>] [--depends <id1,id2>] [--wsjf <cost>/<size>]
```

- **`title`**: Task title / description (required).
- **`--id`**: Explicit task identifier (defaults to kebab-cased title).
- **`--prio`**: Priority level (`P0`, `P1`, `P2`, `P3`). Default `P2`.
- **`--after`**: Places the task immediately after the specified task and adds a dependency on it.
- **`--depends`**: Comma-separated list of prerequisite task IDs.
- **`--wsjf`**: Cost of Delay / Job Size ratio (e.g. `4.0/2.0`).

---

### 3. `dep`
Manages task dependencies with cycle detection.

```bash
todo dep add <task-id> <prerequisite-id>
todo dep rm <task-id> <prerequisite-id>
```

- **`add`**: Links `<prerequisite-id>` as a dependency of `<task-id>`. Rejects the change if a circular dependency cycle is detected.
- **`rm`**: Removes `<prerequisite-id>` from `<task-id>`'s dependencies.

---

### 4. `graph`
Visualizes the backlog DAG and topological execution waves.

```bash
todo graph [--mermaid]
```

- **Default (ASCII Tree):** Displays sequential execution waves with tree branches.
- **`--mermaid`:** Emits valid Mermaid flowchart syntax for markdown documents and documentation.

---

### 5. `status`
Displays progress breakdown, execution waves, and top unblocked tasks.

```bash
todo status
```

---

### 6. `next`
Selects the unblocked task with the highest WSJF score, pages its acceptance card into context, and stages it as an Antigravity artifact.

```bash
todo next
```

---

### 7. `prev`
Produces a 3-line factual summary of the last completed task and its corresponding git commit.

```bash
todo prev
```

---

### 8. `view`
Displays one or more task cards matching the query.

```bash
todo view <query>
```

---

### 9. `edit`
Interactive editing in Vim/Neovim or express non-interactive updates.

```bash
# Interactive editing in tmux popup or terminal
todo edit <query>

# Express operations:
todo edit <query> done            # Mark task completed
todo edit <query> undone          # Reopen task
todo edit <query> P0|P1|P2|P3     # Update priority
todo edit <query> add <text>      # Append acceptance criterion
```

---

### 10. `replan`
Topologically sorts the backlog by WSJF execution waves and rewrites `TODO.md`.

```bash
todo replan
```
