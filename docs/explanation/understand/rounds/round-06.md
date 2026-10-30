# GRILL ROUND 6 -- topic: /understand slash command
# STANCE: long horizon. The current code is evidence, not authority.
#
# KEYS:  ]q / [q  next / previous section
#        <Space>  select the option on this line
#        >>       write a reply under this line
#        :wq      send       :q!  quit without changes, then choose
#
# The recommended option is selected. Change it only if you disagree.
# Write a reply only where you disagree or know more.

## Q1 [design.mermaid-runtime] -- How does the renderer draw Mermaid diagrams?

CONTEXT:
  Verification found that mmdc cannot render here. Puppeteer has no
  Linux arm64 Chrome.
  Debian has chromium-headless-shell 156 (apt, needs sudo once). mmdc
  can use it with a puppeteer config file.
  Mermaid JS in the page renders in the reader's browser. It adds about
  3 MB, vendored once in the shadow root, so it stays offline.

OPTIONS:
  [x] A. Install chromium-headless-shell; fall back to in-page  (RECOMMENDED)
         Fast pages and SVG in the bundle. One sudo apt install.
         Fallback keeps runs from failing.
  [ ] B. In-page Mermaid only
         No system install. Pages draw slower. SVG is not in the bundle
         for agents.
  [ ] C. Pre-render only, fail the run without chromium
         One path. A missing package stops every run.

DIAGRAM:
    A: renderer --mmdc + system chromium--> inline SVG in report
    B: report loads _vendor/mermaid.min.js --> draws in browser
    C: try A; if mmdc fails --> fall back to B (logged)

## Q2 [lens.diff] -- What does the diff lens compare?

CONTEXT:
  No round asked about the diff lens. The draft assumes the rule from
  codemap --diff --ref.
  Uncommitted changes are included, so the report shows work in
  progress.

OPTIONS:
  [x] A. merge-base(REF, HEAD) to working tree  (RECOMMENDED)
         Shows all your local work. Same as codemap. Report can change
         between two runs at one commit.
  [ ] B. merge-base(REF, HEAD) to HEAD
         Committed work only. Repeatable per commit.

## REVIEW

  DESIGN TREE: /understand   (stance: long horizon)

  stance ........................ long horizon
  render.model .................. bundle + fixed renderer        ADR 0001
  orchestration ................. current agent + bg_delegate
  store.location ................ XDG cache, todo-navigator slug
    cache ....................... per commit+lens, latest link
      cache.retention ........... last 5 per lens
  command.surface ............... /understand [topic|pr|diff] + aliases
  delivery ...................... nginx, Parallels network only
    delivery.nginx-mode ......... systemd --user, :8787
      delivery.serve-root ....... /r/ shadow, /src/ ~/projects  ADR 0002
      source.links .............. source views with L<n> ids
    delivery.index .............. generated index pages
  discovery.scope ............... size tiers from codemap pre-scan
  discovery.non-code ............ code / docs / mixed profiles
  design.system ................. Material 3 tokens + SVG icons
  design.interactivity .......... Mermaid SVG + Cytoscape
    design.mermaid-runtime ...... OPEN (Q1)
  anchors ....................... anchors.json, stable ids
  glossary ...................... end of report, patch offer
    glossary.contexts ........... by context, flag collisions
  lens.pr ....................... gh + temp detached worktree
  lens.diff ..................... CONFIRM (Q2)
  lens.topic .................... terms -> seeds -> 1-hop, dim
  ux.progress ................... phase status, URL + summary
  code.home ..................... all in agent-skills
  renderer.lang ................. Python stdlib
  artefacts.adr-home ............ docs/adr/
  metric ........................ agent quiz + owner judgement

  ARTEFACTS (agent-skills repo):
    docs/reference/understand/spec.md           handoff spec (draft)
    docs/reference/understand/GLOSSARY.md       glossary, 18 terms
    docs/explanation/understand/decision-tree.md
    docs/explanation/understand/rounds/         round-01..06
    docs/explanation/understand/c4.md           context + containers
    docs/adr/0001-bundle-and-fixed-renderer.md
    docs/adr/0002-report-server-allow-list.md
    skills/understand/features/understand.feature  7 rules

  VERIFICATION:
    links resolve ............ ok
    Gherkin parses ........... ok (7 rules)
    YAML contract parses ..... ok
    Mermaid renders .......... FAIL: no chromium (see Q1)

  BUILD ORDER (tracer bullets):
    1 renderer + schema + fixture bundle (pytest)
    2 report server + 404/deny probe test
    3 extension + skill, full lens, small repo
    4 planner tiers + docs profile
    5 topic, pr, diff lenses
    6 glossary contexts + agent quiz

  :wq approves. >> notes correct.

## TERMS

  Report: One HTML document that shows a repository, or a part of it,
  for a reader.
    Avoid: visualization, doc, page
  Renderer: The fixed program that turns a bundle into a report.
    Avoid: builder, generator
  Lens: The focus of a report: the full repository, a topic, a pull
  request, or a diff.
    Avoid: mode, filter, scope
  Run: One execution of the command for one commit and one lens. It
  makes one bundle and one report.
