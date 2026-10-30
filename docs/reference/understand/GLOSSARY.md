# Glossary: /understand

**Report**:
One HTML document that shows a repository, or a part of it, for a reader.
_Avoid_: visualization, doc, page

**Bundle**:
The files that the agent writes for one report: a graph, sections, and a glossary.
_Avoid_: output, artifact

**Lens**:
The focus of a report: the full repository, a topic, a pull request, or a diff.
_Avoid_: mode, filter, scope

**Shadow directory**:
A directory outside the repository that holds generated files for that repository.
_Avoid_: cache dir, output dir

**Delegate**:
A read-only background agent that discovers one aspect of the repository.
_Avoid_: subagent, worker

**Renderer**:
The fixed program that turns a bundle into a report.
_Avoid_: builder, generator

**Report server**:
The user-level web server that shows the shadow directory to the host computer.
_Avoid_: web server

**Serve root**:
A directory that the report server is permitted to show.
_Avoid_: whitelist

**Source view**:
A page that shows one cited file, with an id on each line.
_Avoid_: code page, file page

**Anchor**:
A stable id for one node or section that a URL can point to.
_Avoid_: link, bookmark

**Aspect**:
One kind of discovery that a delegate does, for example structure, dependencies, or domain.
_Avoid_: area, stage

**Run**:
One execution of the command for one commit and one lens. It makes one bundle and one report.

**Context**:
A part of a system where each term has one meaning.
_Avoid_: domain, module

**Collision**:
One term that has different meanings in two or more contexts.
_Avoid_: conflict, clash

**Seed node**:
A node that a search finds directly for a topic, before neighbours are added.
_Avoid_: match, hit

**Focus set**:
The nodes that a topic or a pull request makes relevant, plus their direct neighbours.
_Avoid_: highlight set, selection
