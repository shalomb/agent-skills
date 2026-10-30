# GRILL ROUND 4 -- topic: /understand slash command
# STANCE: long horizon. The current code is evidence, not authority.
#
# KEYS:  ]q / [q  next / previous section
#        <Space>  select the option on this line
#        >>       write a reply under this line
#        :wq      send       :q!  quit without changes, then choose
#
# The recommended option is selected. Change it only if you disagree.
# Write a reply only where you disagree or know more.

## Q1 [delivery.serve-root] -- Which directories does the report server expose?

CONTEXT:
  Your $HOME holds live secrets: ~/.ssh/id_ed25519, ~/.aws/credentials,
  ~/.vault-token, ~/.netrc, ~/.pi/agent/auth.json, OAuth token files,
  and several .env files.
  Any device on 10.211.55.0/24 could read them through the server. A
  deny list of dotfiles is easy to get wrong. One missed path leaks a
  key.
  Reports need links to source files. An allow list of roots gives those
  links without the secrets.

OPTIONS:
  [x] A. Allow list: shadow root plus ~/projects  (RECOMMENDED)
         Links to source work. Dotfiles and dot dirs are blocked in both
         roots. New roots are added on purpose.
  [ ] B. All of $HOME with a dotfile deny list
         Any file can be linked. One missed rule leaks a secret to the
         network.
  [ ] C. Shadow root only
         Safest. Source links fall back to editor URIs, not the browser.

DIAGRAM:
    allow list (recommended)          deny list (risky)
    /r/   -> ~/.cache/agent-skills/   /  -> $HOME
    /src/ -> ~/projects/  (no dot)    deny ~ /\.  ; deny .env ...
    default: 404                      default: serve

## Q2 [source.links] -- How do links to code lines resolve?

CONTEXT:
  nginx serves source as plain text, with no line numbers and no #L42
  anchors.
  Anchors (settled) need path and line targets that a browser can open.
  The renderer can make a small source view page for each file it cites,
  with line ids. Only cited files, not the full repo.

OPTIONS:
  [x] A. Renderer makes source views for cited files  (RECOMMENDED)
         Line anchors work offline and in the report style. Adds pages
         per run.
  [ ] B. Link to raw files from the server
         No extra pages. No line anchors.
  [ ] C. Link to the forge (GitHub blob URL at the commit)
         Line anchors for free. Fails for local-only and non-git
         directories.

## Q3 [glossary.contexts] -- How does the glossary handle terms that change meaning by context?

CONTEXT:
  domain-modeling has a convention: GLOSSARY-MAP.md at the root points
  to one GLOSSARY.md per context.
  One term can mean different things in two contexts, for example
  'Account' in billing and in identity.
  The graph already groups nodes by area. A context is a set of areas.

OPTIONS:
  [x] A. Group terms by context; mark collisions  (RECOMMENDED)
         Uses GLOSSARY-MAP.md if present, else infers contexts from
         areas. Collisions are flagged, not merged.
  [ ] B. One flat glossary, one meaning per term
         Simple. Hides real ambiguity.
  [ ] C. Ask the user to name contexts each run
         Precise. Slows every run.

DIAGRAM:
    Glossary (end of report)
      billing:  Account = payer of invoices  [src/billing/..]
      identity: Account = login principal    [src/identity/..]
      ! Account: 2 meanings (collision, links both)

## Q4 [code.home] -- Where does the code live?

CONTEXT:
  The skill goes in agent-skills/skills/understand (shared, versioned).
  Generated commands (/c4) come from commands.json and only forward to a
  skill. /understand needs subcommands, completion and aliases.
  Hand-written commands (/lazygit) also live in
  agent-skills/commands/pi/extensions. /help and /git live only in
  ~/.pi/agent/extensions.

OPTIONS:
  [x] A. All in agent-skills: skill, hand-written extension, renderer  (RECOMMENDED)
         One repo, versioned, shared. Extension must not import local
         _lib (copy what it needs, like lazygit).
  [ ] B. Skill in agent-skills, extension local
         Can reuse local _lib/subcommands.ts. Split across two places.

## Q5 [renderer.lang] -- Which language does the renderer use?

CONTEXT:
  web-presentation build.py is stdlib-only Python. It is tested and
  works.
  Local extensions use TypeScript with bun test.
  The renderer must read the bundle, run mmdc, embed SVG, write HTML,
  source views and the index page.

OPTIONS:
  [x] A. Python stdlib, next to build.py  (RECOMMENDED)
         Shares theme code with web-presentation. No install step.
         pytest is already in use in the repo.
  [ ] B. TypeScript on bun
         Same language as the extension. Adds a runtime dependency to
         the skill.

## TERMS

  Report: One HTML document that shows a repository, or a part of it,
  for a reader.
    Avoid: visualization, doc, page
  Bundle: The files that the agent writes for one report: a graph,
  sections, and a glossary.
    Avoid: output, artifact
  Renderer: The fixed program that turns a bundle into a report.
    Avoid: builder, generator
  Report server: The user-level nginx that serves the shadow directory
  to the host Mac.
    Avoid: web server
  Context: A part of the system where each term has one meaning.
    Avoid: domain, module
  Collision: One term that has different meanings in two or more
  contexts.
    Avoid: conflict, clash
  Source view: A page that the renderer makes for one cited file, with
  an id on each line.
    Avoid: code page, file page
  Serve root: The set of directories that the report server is permitted
  to expose.
    Avoid: whitelist
