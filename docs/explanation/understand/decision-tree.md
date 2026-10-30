# Design tree: /understand

Goal: A slash command that builds an interactive, navigable HTML report of a repository (whole, by topic, by PR, or by diff) to onboard people and agents.
Stance: long horizon

- [settled] stance -- Long horizon. Existing commands and skills are evidence; we may change them.
    Reason: new capability, no plan or branch in flight. Round 1.
- [settled] render.model -- Bundle (graph JSON + Markdown sections + glossary) rendered by one fixed, tested renderer.
    Reason: interactive graphs need structured data; one renderer gives a consistent look. Round 1. ADR: ../../adr/0001-bundle-and-fixed-renderer.md
- [settled] orchestration -- The current agent runs the understand skill and fans out read-only bg_delegate workers, then converges on the bundle.
    Reason: same pattern as /c4; delegates are read-only by construction. Round 1.
- [settled] store.location -- Shadow directory in ${XDG_CACHE_HOME:-~/.cache}/agent-skills/understand/<repo_slug>/, same slug as todo-navigator.
    Reason: reports can be regenerated; one slug convention links todos and reports. Round 1.
- [settled] command.surface -- /understand [topic] with pr and diff subcommands; /understand-pr and /understand-diff are aliases.
    Reason: one entry point with completion, like /git. Round 1.
- [settled] delivery -- Always-on nginx serves the shadow directory, only on the Parallels network (10.211.55.0/24). The agent prints the URL.
    Reason: no $BROWSER in the VM; nginx 1.30 is installed (system unit masked, www-data, blog on :80 all interfaces). Round 2 note.
  - [settled] delivery.nginx-mode -- User-level nginx under a systemd --user unit, port 8787, allow 10.211.55.0/24 only.
      Reason: no sudo, runs as user, blog site untouched. Round 3.
    - [settled] delivery.serve-root -- Allow list: /r/ -> shadow root, /src/ -> ~/projects; dotfiles and dot dirs blocked; default 404.
        Reason: $HOME holds ssh keys, aws creds, vault token, auth.json; a deny list leaks on one miss. Round 4. ADR: ../../adr/0002-report-server-allow-list.md
    - [settled] source.links -- The renderer makes a source view (line ids) for each cited file.
        Reason: line anchors offline and in report style; works for non-git dirs. Round 4.
  - [settled] delivery.index -- Generated index page, global and per repo, same design system.
      Reason: readable start page across many runs. Round 3.
- [settled] discovery.scope -- Size-tiered delegate plan from a codemap pre-scan (small: 3 by aspect; medium: aspects x areas, cap 8; large: areas, cap 12, lens narrows).
    Reason: scales; planner is pure and testable. Round 2.
- [settled] discovery.non-code -- Detect code/docs/mixed; docs profile gives document map, glossary, reading order.
    Reason: one command for all directories, git or not. Round 2.
- [settled] design.system -- Material 3 tokens plus an inline SVG subset of Material Symbols; offline.
    Reason: small, offline, consistent with web-presentation. Round 2.
- [settled] design.interactivity -- Mermaid pre-rendered to inline SVG by mmdc for diagrams; Cytoscape.js vendored once in the shadow root for the graph.
    Reason: each tool for what it does well; offline. Round 3.
  - [settled] design.mermaid-runtime -- Pre-render with mmdc using system chromium-headless-shell (apt); if mmdc fails, fall back to vendored in-page Mermaid and log it.
      Reason: puppeteer has no arm64 Chrome (found in verification); fallback keeps runs from failing. Round 6.
- [settled] anchors -- anchors.json sidecar with stable path-based ids; every node and section has id=<anchor>.
    Reason: agents link by id without parsing HTML. Round 2.
- [settled] glossary -- Glossary section at the end of the report (in the bundle); the report offers a GLOSSARY.md draft as a patch, never writes the repo.
    Reason: repo stays read-only; terms still reach the repo by user choice. Round 3.
  - [settled] glossary.contexts -- Group terms by context (GLOSSARY-MAP.md if present, else inferred from areas); flag collisions, link each meaning.
      Reason: shows real ambiguity instead of hiding it. Round 4.
- [settled] cache -- Keep each run by commit and lens, with a latest symlink per lens.
    Reason: history and comparison; old report usable during a rebuild. Round 2.
  - [settled] cache.retention -- Keep the last 5 runs per lens.
      Reason: bounded disk, enough to compare. Round 3.
- [settled] code.home -- All in agent-skills: skills/understand (skill + renderer), commands/pi/extensions/understand-command.ts (hand-written, self-contained).
    Reason: one versioned repo; same pattern as lazygit. Round 4.
- [settled] renderer.lang -- Python stdlib, next to web-presentation build.py, tested with pytest.
    Reason: shares theme code; no install step. Round 4.
- [settled] lens.pr -- gh pr view metadata plus a temporary detached worktree at the PR head under the shadow dir; the extension does the git step; removed after the run.
    Reason: full files for source views; user checkout untouched; delegates stay read-only. Round 5.
- [settled] lens.diff -- Compare merge-base(<ref>, HEAD) to the current working tree, uncommitted changes included (as codemap --diff --ref).
    Reason: shows all local work; same as codemap. Round 6.
- [settled] lens.topic -- Expand topic to terms, search names and text for seed nodes, add 1-hop neighbours as the focus set; dim the rest.
    Reason: finds synonyms; keeps the full map for orientation. Round 5.
- [settled] ux.progress -- Status line per phase (plan, discover, converge, render), then URL and a 5-line summary.
    Reason: long runs need a sign of progress; URL is the main result. Round 5.
- [settled] artefacts.adr-home -- New docs/adr/ at repo level. ADR: ../../adr/0001-bundle-and-fixed-renderer.md, ../../adr/0002-report-server-allow-list.md
    Reason: standard home, others can add. Round 5.
- [settled] metric -- Both: a fixed agent quiz with vs without the report, and the user's judgement after use on 3 repos.
    Reason: repeatable agent signal plus real human signal. Round 3.
