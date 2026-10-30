# understand

Renderer for `/understand` reports. An agent writes a **bundle**; one fixed
renderer turns it into a report that opens offline. Agents never write HTML
([ADR 0001](../../docs/adr/0001-bundle-and-fixed-renderer.md)).

## Bundle format (schema version 1)

```
bundle/
  graph.json      required  {"schema_version": 1, "title"?, "nodes": [...], "edges": [...]}
  sections/*.md   required  at least one; shown in file-name order
  anchors.json    optional  {"<id>": {"path", "line"}}  extra cited places
  glossary.json   optional  {"contexts": [{"name", "terms": [{"term", "meaning"}]}]}
```

- node: `{"label", "path", "kind"?, "symbol"?, "line"?, "summary"?}`. Its anchor id is
  `path` or `path::symbol`, so it does not change when files are reordered.
- edge: `{"source", "target", "kind"?}`, where both are node anchor ids.
- section anchor id: the file name without order prefix and extension
  (`02-configuration.md` is `configuration`). `graph` and `glossary` belong to the renderer.
- The renderer refuses a bundle with an unknown `schema_version`, a node without a
  `path`, or any `.html` file. The run names the faulty part and writes nothing.

## Run

```
cd skills/understand/scripts
python -m understand_render BUNDLE_DIR OUT_DIR --source-root REPO_DIR
# or: python scripts/render.py BUNDLE_DIR OUT_DIR --source-root REPO_DIR
```

Options: `--mmdc PATH` and `--chromium PATH`. Mermaid diagrams are drawn ahead of time with
`mmdc` and `chromium-headless-shell`; if that fails the vendored in-page Mermaid draws
them and `render.log` says so.

`OUT_DIR` gets `report.html`, `src/<path>.html` (a source view with an id `L<n>` on each
line), `anchors.json` (`{id: {url, path, line}}`) and `render.log`. The per-repo list of runs
is written by `understand_render.index.write_repo_index(repo_dir, repo_name)`.

## Test

```
cd skills/understand
uv run pytest tests/renderer -q
```

Browser scenarios need `chromium-headless-shell` and are skipped without it.
Scenarios with `@wip` belong to later build steps and are not collected as passing.
