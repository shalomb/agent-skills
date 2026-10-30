# GRILL ROUND 2 -- topic: /understand slash command
# STANCE: long horizon. The current code is evidence, not authority.
#
# KEYS:  ]q / [q  next / previous section
#        <Space>  select the option on this line
#        >>       write a reply under this line
#        :wq      send       :q!  quit without changes, then choose
#
# The recommended option is selected. Change it only if you disagree.
# Write a reply only where you disagree or know more.

## Q5 [delivery] -- How does the user open the report?

CONTEXT:
  No $BROWSER in the VM. The host reaches the VM on 10.211.55.3
  (Parallels) and 100.99.83.53 (tailscale).
  Port 443 on tailscale is already in use. pi-moe runs as a user systemd
  service, so that pattern exists.
  The host home is mounted at /media/psf/Home. A file copy there needs
  no server.
  One static server for the whole shadow directory also serves todo
  cards later.

OPTIONS:
  [x] A. Always-on static server on the Parallels NIC  (RECOMMENDED)
         Agent prints a URL. One service, index page of all reports.
         Needs a unit file and a free port.
         I believe we have nginx installed - but we need to expose a path to
         the $XDG dir (and only to the parallels network to allow the host Mac
             to access the site)
  [ ] B. Copy report to host home, print path
         No server. Works only on this VM layout. Host opens file://.
  [ ] C. tailscale serve on a new port
         Reachable from any device. Depends on tailscale and its free
         ports.

DIAGRAM:
    shadow dir (~/.cache/agent-skills/)
       |
       +-- A: static server on 10.211.55.3:<port>  --> host browser
       |      (bun, user systemd unit, index of reports)
       +-- B: copy report to /media/psf/Home/...   --> file:// on host
       +-- C: tailscale serve                      --> any device

## Q2 [discovery.scope] -- How do we budget delegates on a large repo?

CONTEXT:
  bg_delegate has a cap of 120 tool calls and 24 turns per delegate.
  codemap . shows file counts for each directory in one call.
  A large repo (10k+ files) needs partition by area, not one delegate
  per aspect.
  A fixed count is predictable. A size-driven count scales.

OPTIONS:
  [x] A. Size-tiered plan from a codemap pre-scan  (RECOMMENDED)
         Scales. Needs a tested planner that maps size to a delegate
         plan.
  [ ] B. Fixed three delegates by aspect
         Simple. Large repos get shallow results.
  [ ] C. Ask the user for areas each time
         Precise. Slows every run with a prompt.

DIAGRAM:
    codemap . --> size + top dirs
        |
        small  (<1k files): 3 delegates by aspect
        medium (<10k):      aspects x top-level areas (cap 8)
        large  (>10k):      areas only, depth 2, cap 12,
                            lens narrows to touched areas

## Q3 [discovery.non-code] -- Are docs or content directories in scope?

CONTEXT:
  Some directories hold only docs, notes, or context, and some are not
  git repos.
  The same bundle format works: nodes are documents and headings, edges
  are links.
  A pure-docs repo gets a document map, a glossary, and a reading order
  instead of a dependency graph.

OPTIONS:
  [x] A. Detect content type, use a docs profile  (RECOMMENDED)
         One command for code and docs. The planner needs a
         code/docs/mixed detector.
  [ ] B. Code repos only, say no for others
         Less work. Docs repos get no report.

## Q4 [design.system] -- Which design system does the report use?

CONTEXT:
  The report must open offline, like web-presentation output.
  Material Symbols as a web font is 1 to 3 MB. A subset of 40 to 60
  icons as inline SVG is a few KB.
  web-presentation has theme.css. A shared token set keeps both outputs
  consistent.

OPTIONS:
  [x] A. Material 3 tokens, inline SVG icon subset  (RECOMMENDED)
         Offline, small, consistent. Icons limited to a curated subset.
  [ ] B. Reuse web-presentation theme.css as is
         Zero new design work. No icons, no graph styles.
  [ ] C. Material web components from CDN
         Full Material. Needs network. Breaks offline rule.

## Q5 [anchors] -- How do other agents link into a report?

CONTEXT:
  Other agents need stable links into the report and into the code.
  A graph.json in the bundle already holds nodes with file paths and
  symbols.
  An anchors index lets a todo card or an ADR link to a report section
  by id.

OPTIONS:
  [x] A. anchors.json sidecar with stable ids  (RECOMMENDED)
         Agents link by id. Ids must stay stable across runs
         (path-based).
  [ ] B. HTML ids only, no sidecar
         Less to maintain. Agents must parse HTML to find links.

DIAGRAM:
    bundle/
      graph.json     nodes: {id, kind, path, line, label}
      anchors.json   id -> {url: report.html#id, path, line}
    report.html      every node and section has id=<anchor id>

## Q6 [cache] -- How are repeated runs stored?

CONTEXT:
  A full run on a large repo can take many minutes.
  git rev-parse HEAD and the lens give a natural key for a run.
  An old report is still useful while a new one builds.

OPTIONS:
  [x] A. Keep each run by commit and lens, latest symlink  (RECOMMENDED)
         History of reports. Disk grows. Easy to compare two runs.
  [ ] B. Overwrite one report per lens
         Small on disk. No history.
  [ ] C. Incremental update by changed files
         Fast reruns. Complex merge logic in the bundle.

## TERMS

  Report: One HTML document that shows a repository, or a part of it,
  for a reader.
    Avoid: visualization, doc, page
  Bundle: The files that the agent writes for one report: a graph,
  sections, and a glossary.
    Avoid: output, artifact
  Lens: The focus of a report: the full repository, a topic, a pull
  request, or a diff.
    Avoid: mode, filter, scope
  Shadow directory: A directory outside the repository that holds
  generated files for that repository.
    Avoid: cache dir, output dir
  Delegate: A read-only background agent that discovers one aspect of
  the repository.
    Avoid: subagent, worker
  Renderer: The fixed program that turns a bundle into a report.
    Avoid: builder, generator
  Anchor: A stable id for one node or section that a URL can point to.
    Avoid: link, bookmark
  Aspect: One kind of discovery that a delegate does: structure,
  dependencies, or domain.
    Avoid: area, stage
  [?] Run: <not sure. Reply with >> to define it.>
