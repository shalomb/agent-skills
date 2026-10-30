# GRILL ROUND 5 -- topic: /understand slash command
# STANCE: long horizon. The current code is evidence, not authority.
#
# KEYS:  ]q / [q  next / previous section
#        <Space>  select the option on this line
#        >>       write a reply under this line
#        :wq      send       :q!  quit without changes, then choose
#
# The recommended option is selected. Change it only if you disagree.
# Write a reply only where you disagree or know more.

## Q1 [lens.pr] -- How does the pr lens get the PR content?

CONTEXT:
  All your remotes are on GitHub. gh is authenticated as shalomb.
  Delegates are read-only. They cannot check out a branch in your
  working tree.
  A diff alone shows changed lines but not the code around them. A
  worktree at the PR head gives full files for source views.

OPTIONS:
  [x] A. gh metadata plus a temporary detached worktree  (RECOMMENDED)
         Full files at the PR head. Your checkout is not touched.
         Extension does the git step, not delegates.
  [ ] B. gh pr diff only
         No git changes. Source views show only diff hunks.
  [ ] C. Use the current checkout as is
         Simplest. Wrong if you are not on the PR branch.

DIAGRAM:
    /understand pr 123
      gh pr view 123 --json (title, body, files, base, head)
      git worktree add --detach <shadow>/wt/pr-123 <head sha>
      delegates read the worktree; diff = base...head
      after the run: git worktree remove

## Q2 [lens.topic] -- How does the topic lens choose the relevant nodes?

CONTEXT:
  A topic is free text, for example 'auth' or 'how billing retries
  work'.
  Name search (rg, symbol_search) finds literal hits. It misses
  synonyms.
  An agent pass can expand the topic to terms, then search, then rank.
  The result is a seed set of nodes. The graph adds their neighbours.

OPTIONS:
  [x] A. Expand terms, search, add 1-hop neighbours; dim the rest  (RECOMMENDED)
         Finds synonyms. Keeps the full map for orientation. One extra
         agent step.
  [ ] B. Literal search only
         Fast and predictable. Misses related code with other names.
  [ ] C. Show only the focus set
         Small report. Reader loses the context of the full map.

DIAGRAM:
    topic --> expand to terms (glossary, synonyms)
          --> search names + text --> seed nodes
          --> graph: add 1-hop neighbours --> focus set
    report: focus set highlighted, rest dimmed, not removed

## Q3 [ux.progress] -- What does the user see during and after a run?

CONTEXT:
  A full run can take many minutes. The session is busy during the run
  (orchestration is settled).
  pi shows a status line and notify messages. bg_delegate shows tasks in
  the footer dock.
  The report URL is the main result.

OPTIONS:
  [x] A. Phase status line, then URL and 5-line summary  (RECOMMENDED)
         You see plan, discover, converge, render. The end message gives
         the URL and key facts.
  [ ] B. URL only at the end
         Quiet. No sign of progress on long runs.

## Q4 [artefacts.adr-home] -- Where do the ADRs go?

CONTEXT:
  This repo uses Diataxis under docs/. It has no ADR directory.
  Skills with acceptance scenarios keep them in skills/<name>/features/.
  Two decisions pass the ADR test: render.model (bundle plus fixed
  renderer) and delivery.serve-root (allow list).

OPTIONS:
  [x] A. New docs/adr/ at repo level  (RECOMMENDED)
         Standard home. Other skills can add ADRs later.
  [ ] B. skills/understand/docs/adr/
         ADRs stay with the skill. Not found by readers of docs/.

DIAGRAM:
    docs/reference/understand/spec.md         handoff spec
    docs/reference/understand/GLOSSARY.md     glossary (moved)
    docs/explanation/understand/decision-tree.md + rounds/
    docs/explanation/understand/c4.md         architecture views
    docs/adr/0001-*.md, 0002-*.md             ADRs   <- this question
    skills/understand/features/*.feature      acceptance scenarios

## TERMS

  Report: One HTML document that shows a repository, or a part of it,
  for a reader.
    Avoid: visualization, doc, page
  Lens: The focus of a report: the full repository, a topic, a pull
  request, or a diff.
    Avoid: mode, filter, scope
  Delegate: A read-only background agent that discovers one aspect of
  the repository.
    Avoid: subagent, worker
  Run: One execution of the command for one commit and one lens. It
  makes one bundle and one report.
  Focus set: The nodes that a topic or a pull request makes relevant,
  plus their direct neighbours.
    Avoid: highlight set, selection
  Seed node: A node that a search finds directly for a topic, before
  neighbours are added.
    Avoid: match, hit
