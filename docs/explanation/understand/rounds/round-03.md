# GRILL ROUND 3 -- topic: /understand slash command
# STANCE: long horizon. The current code is evidence, not authority.
#
# KEYS:  ]q / [q  next / previous section
#        <Space>  select the option on this line
#        >>       write a reply under this line
#        :wq      send       :q!  quit without changes, then choose
#
# The recommended option is selected. Change it only if you disagree.
# Write a reply only where you disagree or know more.

## Q1 [delivery.nginx-mode] -- Which nginx instance serves the reports?

CONTEXT:
  nginx 1.30 is installed. The system unit is masked. It runs as
  www-data. The default site serves the blog on :80 on all interfaces.
  www-data can read ~/.cache today (mode 755), but the same is true for
  all of your home.
  A user-level nginx runs as you, with its own config, pid and logs
  under XDG dirs. It needs a port above 1024. It does not change the
  blog site.

OPTIONS:
  [x] A. User-level nginx, systemd --user unit  (RECOMMENDED)
         No sudo. Runs as you. Blog site stays as is. Needs a port such
         as 8787.
>> Ok, if we're doing this - can we expose all of $HOME through nginx?
>> This will allow us to serve any file and hyperlinks too across the fs
>> rooted at $HOME right?
  [ ] B. System nginx, new vhost
         One nginx for all sites. Needs sudo and an unmask. www-data
         reads your home.
  [ ] C. Start nginx only on demand
         No idle process. The URL fails after you close it. More state
         to manage.

DIAGRAM:
    A: systemd --user nginx -c ~/.config/understand/nginx.conf
         listen 10.211.55.3:8787;  allow 10.211.55.0/24; deny all;
         root ~/.cache/agent-skills/;  autoindex on;
    B: /etc/nginx/sites-enabled/understand  (unmask system unit)
         same listen + allow; runs as www-data; needs sudo

## Q2 [delivery.index] -- What does the root URL show?

CONTEXT:
  The shadow root holds todos/ and understand/ for many repos.
  autoindex gives a plain file list at no cost.
  A generated index.html can show each repo, lens, and run with links to
  the latest report.

OPTIONS:
  [x] A. Generated index page per repo and global  (RECOMMENDED)
         Readable start page in the same design system. The renderer
         must update it after each run.
  [ ] B. nginx autoindex only
         No code. Plain file list. Hard to read with many runs.

## Q3 [design.interactivity] -- Which technology draws diagrams and the graph?

CONTEXT:
  mmdc (mermaid-cli) and plantuml are installed. No browser, d2 or
  graphviz.
  The report is offline. Libraries must be inline in the HTML or
  vendored next to it.
  Mermaid draws C4 and flow diagrams well but does not support pan,
  filter or expand on large graphs.
  Cytoscape.js (about 400 KB) gives an interactive graph with filter,
  search and click-to-open.

OPTIONS:
  [x] A. Mermaid SVG for diagrams, Cytoscape for the graph  (RECOMMENDED)
         Best of each. Two technologies. Pre-render keeps the page fast.
  [ ] B. Mermaid only, rendered in the page
         One technology. Large graphs become hard to read. Mermaid JS is
         about 3 MB.
  [ ] C. D3 custom graph
         Full control. Much more code to write and test.

DIAGRAM:
    report.html
      C4 / sequence / flow : Mermaid, pre-rendered to inline SVG by mmdc
      dependency graph      : Cytoscape.js, vendored once in shadow root
      every node            : click -> section anchor or source link

## Q4 [glossary] -- Where do generated glossary terms go?

CONTEXT:
  domain-modeling writes GLOSSARY.md in the repo, with _Avoid_ lines.
  /understand is read-only on the repo. Delegates cannot write.
  Generated terms can link to the line in code or docs that defines
  them.

OPTIONS:
  [x] A. Glossary in the bundle; propose repo glossary as a patch  (RECOMMENDED)
         Repo stays clean. The report offers a GLOSSARY.md draft that
         the user can apply.
>> I guess this is probably best placed at the end of the report.
>> How do we handle domain boundaries where terms can differ depending ont he
>> domain and context?
  [ ] B. Bundle glossary only
         Simplest. Terms never reach the repo.
  [ ] C. Write GLOSSARY.md into the repo
         Terms live with code. Breaks the read-only rule.

## Q5 [cache.retention] -- How many runs do we keep?

CONTEXT:
  Each run is kept by commit and lens, with a latest symlink.
  A run holds the bundle and one HTML file, likely 1 to 5 MB.

OPTIONS:
  [x] A. Keep the last 5 runs per lens  (RECOMMENDED)
         Bounded disk. Enough history to compare.
  [ ] B. Keep all, prune by command
         Full history. Disk grows until you prune.
  [ ] C. Keep only latest
         Smallest. No comparison.

## Q6 [metric] -- How do we know the report helps onboarding?

CONTEXT:
  The goal is onboarding people and agents.
  Without a check, we cannot say that the report helps.
  A cheap proxy: a fresh agent answers a fixed set of questions about
  the repo, with and without the report.

OPTIONS:
  [ ] A. Agent quiz: answers with vs without report
         Repeatable and cheap. Tests agent onboarding more than human.
  [ ] B. Your judgement after use on 3 repos
         Real signal for humans. Not repeatable.
  [x] C. Both  (RECOMMENDED)
         Best signal. More work before release.

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
  Renderer: The fixed program that turns a bundle into a report.
    Avoid: builder, generator
  Anchor: A stable id for one node or section that a URL can point to.
    Avoid: link, bookmark
  Run: One execution of /understand for one commit and one lens. It
  makes one bundle and one report.
  Report server: The user-level nginx that serves the shadow directory
  to the host Mac.
    Avoid: web server
