---
name: serve-artefacts
description: 'Publish files (HTML, SVG, PNG, Markdown, JSON) from a worktree or cache to the user''s existing report server and print links that open from the Mac over the Parallels or Tailscale network. Triggers on: ''serve this'', ''open on my mac'', ''give me a link'', ''publish the diagram'', ''view from the host''.'
---

# Serve artefacts

Reuses the user-level nginx that the `understand` skill runs. It starts nothing. The port and addresses are read from the running config, never assumed.

```bash
python3 ~/.pi/agent/skills/serve-artefacts/scripts/publish.py --name <folder> [--title T] <file>...
```

- Copies files to `~/.cache/agent-skills/po/<folder>/` and writes an `index.html` that shows images inline. Prints one folder URL and one URL per file, for each network found.
- **Copies, not symlinks:** the server refuses symlinks. **No dot paths:** any segment starting with a dot returns 404, so never serve from `.worktrees` or `.git`; the script copies out, which avoids it.
- Allowed types only: html, svg, png, jpg, md, txt, json, css, js, mmd. Anything else is skipped with a message.
- A re-publish with the same `--name` replaces the folder, so stale files do not linger.
- Access is limited by the server to the Parallels subnet and the tailnet. Content is a snapshot, not a validated record.
- Never publish secrets, `.netrc`, tokens or `.env` files. Check what you pass in.
- If the script says no server is running, tell the user; the `understand` skill documents how to start it. Do not start one unasked.

## Serve in place (no copy)

Content that already lives under `~/.cache/agent-skills/` (for example a `teach` workspace at `teach/<topic>/`) is already reachable at `/r/`. Link it, do not copy it, so the page stays live:

```bash
python3 ~/.pi/agent/skills/serve-artefacts/scripts/urls.py <path>...
```

- Prints one `Parallels:` and one `Tailnet:` URL per path. A directory gets a trailing slash and the server's autoindex.
- Refuses a path outside the root, behind a dot segment, through a symlink at any level, or missing, with a message. Starts nothing.
- Relative links inside the content keep working, so a lesson at `lessons/0001-x.html` finds `../assets/style.css`.
- Use `publish.py` instead for files elsewhere (a worktree, `~/.cache/jira`): it copies them into `/r/po/<name>/`.

