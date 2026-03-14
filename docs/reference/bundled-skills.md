# Reference: Bundled Skills

Claude Code ships with five built-in skills available in every session. Unlike custom commands, bundled skills are prompt-based - they give Claude a detailed playbook and let it orchestrate the work using its tools.

## Built-in Skills

### /simplify
Reviews your recently changed files for code reuse, quality, and efficiency issues, then fixes them.

**Use when:**
- You've just implemented a feature or bug fix
- You want to clean up your work before committing
- You need code review focused on maintainability

**Process:**
- Spawns three review agents in parallel:
  1. **Code Reuse Reviewer** - Identifies reusable code patterns
  2. **Code Quality Reviewer** - Checks for quality issues
  3. **Efficiency Reviewer** - Finds performance bottlenecks
- Aggregates findings from all three agents
- Applies fixes to your code

**Example usage:**
```
/simplify
/simplify focus on memory efficiency
/simplify in the utils/ directory
```

### /batch
Orchestrates large-scale changes across a codebase in parallel.

**Use when:**
- Making widespread refactoring changes
- Migrating between frameworks or libraries
- Applying consistent changes across many files
- The change can be decomposed into independent units

**Process:**
1. **Analyze** - Understands the refactoring request
2. **Plan** - Researches the codebase structure
3. **Decompose** - Breaks work into 5-30 independent units
4. **Present** - Shows plan for your approval
5. **Execute** - Spawns one agent per unit in isolated git worktrees
6. **Review** - Each agent implements, tests, and opens a PR

**Requirements:**
- Git repository (required)
- Work must be decomposable into independent units

**Example usage:**
```
/batch migrate src/ from Solid to React
/batch update all imports to use new package name
/batch refactor all classes to use hooks
```

### /debug
Troubleshoots your current Claude Code session.

**Use when:**
- Something isn't working as expected
- You want to understand what Claude is doing
- You need to diagnose a session issue

**Process:**
- Reads the session debug log
- Analyzes what went wrong
- Optionally focuses on specific issues you describe

**Example usage:**
```
/debug
/debug Skill not triggering automatically
/debug Why did the last command fail?
```

### /loop
Runs a prompt repeatedly on an interval while the session stays open.

**Use when:**
- Polling for completion status
- Running periodic checks
- Monitoring deployments or PRs
- Re-running another skill on a schedule

**Process:**
1. **Parse** - Understands the interval specification
2. **Schedule** - Sets up a recurring cron task
3. **Confirm** - Shows you the cadence
4. **Execute** - Runs the prompt repeatedly

**Interval formats:**
- Minutes: `5m`, `30m`
- Hours: `1h`, `2h`
- Time of day: `0900`, `1430`

**Example usage:**
```
/loop 5m check if the deploy finished
/loop 30m check PR status
/loop 1h run test suite
```

### /claude-api
Loads Claude API reference material for your project's language.

**Supported languages:**
- Python
- TypeScript/JavaScript
- Java
- Go
- Ruby
- C#
- PHP
- cURL

**What it provides:**
- API reference for your language
- Agent SDK reference (Python and TypeScript)
- Tool use documentation
- Streaming examples
- Batch operations
- Structured outputs
- Common pitfalls and solutions

**Automatic activation:**
This skill activates automatically when your code imports:
- `anthropic` (Python)
- `@anthropic-ai/sdk` (Node.js)
- `claude_agent_sdk` (Python)

**Example usage:**
```
/claude-api
/claude-api Show me how to use streaming
/claude-api Tool use best practices
```

## Key Characteristics

### Parallel Execution
Some bundled skills (like `/simplify` and `/batch`) spawn multiple agents working in parallel, making them much faster than sequential approaches.

### Prompt-Based Logic
Unlike built-in commands which execute fixed logic, bundled skills use Claude's reasoning to adapt to your specific context and codebase.

### Tool Orchestration
Bundled skills can coordinate multiple tool calls, read files, execute commands, and adapt based on results.

## Invocation

You invoke bundled skills the same way as custom skills:

```bash
# Direct invocation with slash command
/skill-name [optional arguments]

# Example
/simplify
/batch migrate to React
/loop 5m check deploy status
```

## Limitations

- Bundled skills are only available in Claude Code sessions
- They require an active session to run
- Some (like `/batch`) require specific project setup (Git repos)
- All bundled skills respect your custom skill restrictions

## See Also

- [How-to: Advanced Patterns](../how-to/advanced-patterns.md) - Creating skills that work like bundled skills
- [Reference: Frontmatter](./frontmatter.md) - Control whether Claude can invoke skills
