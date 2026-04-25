# Codemap API Reference

## MCP Tools

When `codemap mcp` server is configured:

| Tool | Use for |
|---|---|
| `get_structure` | Project tree |
| `get_dependencies` | Dependency flow + hubs |
| `get_diff` | Changed files with impact |
| `find_file` | Search by filename |
| `get_importers` | Who imports a file |
| `get_hubs` | All hub files |
| `get_file_context` | Full context for one file |
| `get_handoff` | Build/read handoff artifact |
| `get_working_set` | Files edited this session |
| `list_skills` | Available skills (metadata) |
| `get_skill` | Full skill instructions |
| `get_activity` | Recent coding activity |
| `start_watch` / `stop_watch` | Control file-watch daemon |
| `status` | Verify MCP connection |
| `list_projects` | Discover projects |

## HTTP API

When `codemap serve --port 9471` is running:

| Endpoint | Returns |
|---|---|
| `GET /api/context?intent=...` | Full context envelope |
| `GET /api/context?compact=true` | Minimal token-saving envelope |
| `GET /api/skills` | All skills with metadata |
| `GET /api/skills/<name>` | Full skill body |
| `GET /api/working-set` | Files edited this session |
| `GET /api/health` | Server health check |

## Output interpretation

**Tree view** (`codemap .`): ⭐ marks top 5 largest source files. Directories with a single subdirectory are flattened.

**Deps** (`codemap --deps`): External deps grouped by language. `HUBS:` section lists most-imported files (3+ importers = high blast radius).

**Diff** (`codemap --diff`): `(new)` = untracked, `✎` = modified, `(+N -M)` = line delta. ⚠️ on hub files.

**Importers** (`codemap --importers <file>`): All files importing this one. 3+ = hub. 8+ = critical.
