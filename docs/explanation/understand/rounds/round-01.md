# GRILL ROUND 1 -- topic: /understand slash command
# STANCE: long horizon. The current code is evidence, not authority.
#
# KEYS:  ]q / [q  next / previous section
#        <Space>  select the option on this line
#        >>       write a reply under this line
#        :wq      send       :q!  quit without changes, then choose
#
# The recommended option is selected. Change it only if you disagree.
# Write a reply only where you disagree or know more.

## Q1 [stance] -- How much authority does the current code have?

CONTEXT:
  This is a new capability. No plan or branch exists.
  The existing commands (/c4, /codemap, /help, /git lg) are evidence of
  patterns, not rules.

OPTIONS:
  [x] A. Long horizon  (RECOMMENDED)
         Code is evidence. We can change existing skills and extensions
         to fit.
  [ ] B. Mid-execution
         Code is the foundation. New work must fit existing patterns as
         they are.

## Q2 [render.model] -- What does the agent produce, and what makes the HTML?

CONTEXT:
  web-presentation already builds offline HTML from Markdown (build.py,
  theme.css).
  codemap gives text only (tree, deps, diff). No JSON.
  Interactive graphs (filter, click, expand) need structured data, not
  prose.
  A fixed renderer gives one consistent look across reports.

OPTIONS:
  [x] A. Bundle: graph JSON plus Markdown sections  (RECOMMENDED)
         Agent writes data and prose. One renderer makes the HTML.
         Consistent and reusable. More up-front build.
  [ ] B. Markdown with Mermaid only
         Reuse build.py as is. Fast to make. Weak interactivity, no
         clickable graph.
  [ ] C. Agent writes raw HTML
         Full freedom. Each report looks different. Hard to test. Costly
         in tokens.

DIAGRAM:
    delegates --> bundle/          renderer        report.html
                 graph.json  --->  (fixed,  --->   nav + graph +
                 sections/*.md    tested)         sections +
                 glossary.md                      glossary

## Q3 [orchestration] -- Who runs the discovery delegates?

CONTEXT:
  /understand needs an LLM, so it cannot be a no-agent-turn popup like
  /git lg.
  /c4 and /codemap send a /skill: message to the current agent.
  bg_delegate gives read-only delegates seeded with the session.
  subagent needs subagents_enable.
  A detached child pi (bg_run pi -p) keeps the session free but loses
  session context.

OPTIONS:
  [x] A. Current agent orchestrates with bg_delegate  (RECOMMENDED)
         Same pattern as /c4. Session is busy until done. Delegates are
         read-only by design.
  [ ] B. Detached child pi in background
         Session stays free. No session context. Harder to steer and to
         debug.
  [ ] C. Current agent, subagents extension
         Specialist roles possible. Needs subagents_enable. Not
         read-only by default.

DIAGRAM:
    /understand [lens] --> current agent (skill: understand)
                       |-- bg_delegate: structure
                       |-- bg_delegate: dependencies
                       |-- bg_delegate: domain + glossary
                       '-- bg_delegate: lens (topic/pr/diff)
                     converge --> bundle --> renderer --> report

## Q4 [store.location] -- Where does the report live?

CONTEXT:
  todo-navigator uses
  ${XDG_CACHE_HOME:-~/.cache}/agent-skills/todos/<repo_slug>/.
  The same slug lets todo cards and reports link to each other.
  A report is costly to make but can be made again. XDG says cache is
  for data that can be made again.

OPTIONS:
  [x] A. XDG cache, next to todos  (RECOMMENDED)
         Same slug and same layout as todo-navigator. A cache clean
         removes reports.
  [ ] B. XDG data home
         Survives cache clean. A second slug convention to keep in sync.
  [ ] C. XDG config home
         Config is for settings, not output. Backup tools copy it.

## Q5 [command.surface] -- One command with subcommands, or separate commands?

CONTEXT:
  /git uses a subcommand tree with completion (since, diff, lg).
  You asked for /understand, /understand-pr and /understand-diff.
  Aliases cost little: /lazygit and /lg share one spec.

OPTIONS:
  [x] A. /understand with pr and diff subcommands, plus aliases  (RECOMMENDED)
         One entry point with completion. /understand-pr and
         /understand-diff stay as aliases.
  [ ] B. Three separate commands
         Simple. No shared completion. Three places to change.

## Q6 [delivery] -- How does the user open the report?

CONTEXT:
  A tmux popup cannot show HTML.
  This machine is a VM. $BROWSER or xdg-open can open a file on the
  guest.
  A short terminal summary in a popup fits the existing /help pattern.

OPTIONS:
  [ ] A. Open in browser, show summary in popup  (RECOMMENDED)
         Report opens in $BROWSER or xdg-open. Popup shows the path and
         a text summary. Falls back to notify.
  [x] B. Open in browser only
         Simplest. No terminal view of the result.
         We're in a VM and don't have a $BROWSER.
         Can we serve the html on localhost and open a remote browser? That
         would be a good option.
  [ ] C. Serve on localhost
         Works for a remote browser. A process to manage.

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
  [?] Anchor: <not sure. Reply with >> to define it.>
  [?] Repo slug: <not sure. Reply with >> to define it.>
