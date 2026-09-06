# Todo Navigator — CLI Reference

The `todo` CLI provides task backlog navigation, dependency management, and interactive editing with zero repository pollution.

## Global Options

- `--shadow`: Force operations against user cache (`~/.cache/agent-skills/todos/<repo_slug>/`). Default when no repo `TODO.md` is present.
- `-h`, `--help`: Display help and command usage.

---

## Subcommands

### 1. `list`
Prints concise task heading lines grouped by markdown section without dumping full markdown bodies.

```bash
todo list [query] [--id]
```

- **Without arguments:** Lists all tasks in active backlog, grouped under their markdown section headers.
- **With `query`:** Filters tasks matching by task ID, title substring, or markdown section name (e.g. `todo list critical`).
- **`--id`**: Include the generated task ID slug in the output (e.g. `[fix-crash]`).

**Output format:**
```text
## 🔴 CRITICAL
  [ ] [P0] Fix startup crash (after: db-init)

## 🟡 HIGH
  [ ] [P1] Add export report
  [x] [P1] Project Scaffolding
```

---

### 2. `add`
Creates a new task in `TODO.md` and automatically scaffolds a BDD task card in `tasks/<id>.md`.

```bash
todo add "<title>" [--id <id>] [--prio P0-P3] [--section <heading>] [--after <id>] [--depends <id1,id2>] [--wsjf <cost>/<size>]
```

- **`title`**: Task title / description (required).
- **`--id`**: Explicit task identifier (defaults to a clean, capped kebab-cased slug).
- **`--prio`**: Priority level (`P0`, `P1`, `P2`, `P3`). Default `P2`.
- **`--section`**: Markdown section heading under which to insert the task (e.g. `CRITICAL` or `🟡 HIGH`).
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
# Edit master backlog (TODO.md) in tmux popup or terminal
todo edit

# Interactive editing of matching task cards in tmux popup or terminal
todo edit <query>

# Express operations:
todo edit <query> done            # Mark task completed
todo edit <query> undone          # Reopen task
todo edit <query> P0|P1|P2|P3     # Update priority
todo edit <query> add <text>      # Append acceptance criterion
```

- **Without arguments (`todo edit`):** Opens the master `TODO.md` file in `$EDITOR` / tmux popup.
- **With `<query>`:** Smart-matches task cards. If multiple match, opens all matching files simultaneously (`vi card1 card2...`).
- **With express ops:** Applies non-interactive in-place modifications to criteria or completion status.

---

### 10. `replan`
Topologically sorts the backlog by WSJF execution waves and rewrites `TODO.md`.

```bash
todo replan
```
