# 0004. Client-side dynamic catalog with report.html default index

- Status: Accepted
- Date: 2026-11-02
- Context: /understand design session, nodes `index.dashboard`, `nginx.default-file` ([decision tree](../explanation/understand/decision-tree.md))

| Y-statement | |
| :-- | :-- |
| In the context of | browsing and discovering reports served over the local nginx report server |
| facing | inconvenient manual URL typing and slow, unstyled nginx directory listings |
| we decided for | a client-side SPA catalog fetching `catalog.json` and configuring `report.html` as the default nginx directory index |
| and neglected | a static HTML dashboard rebuilt on every run; raw nginx directory auto-indexing |
| to achieve | instant search, filtering across historical runs, and seamless direct URL navigation |
| accepting that | the browser must parse `catalog.json` and atomic file locking is needed on catalog updates |
| because | an interactive catalog provides immediate discovery without rebuilding global HTML on each run, while `index report.html` eliminates broken directory URLs |
| revisit when | historical runs exceed 10,000 entries and client-side JSON filtering causes browser lag |

## Decision drivers

- DRV-01 Instant discovery of past runs across all repositories and lenses.
- DRV-02 Clean directory URL resolution without requiring explicit `report.html` in the path.
- DRV-03 Safe concurrent writes across parallel analysis sessions.
- DRV-04 Zero runtime backend or application server required.

## Options

| Option | DRV-01 | DRV-02 | DRV-03 | DRV-04 |
| :-- | :-: | :-: | :-: | :-: |
| **Client-side catalog + report.html index** | yes | yes | yes | yes |
| Static HTML rebuild on every run | no | yes | no | yes |
| Raw nginx auto-index | no | no | yes | yes |

## Consequences

- Nginx configuration specifies `index report.html index.html;` in the `/r/` location.
- The shadow root hosts a lightweight static `index.html` SPA fetching `catalog.json`.
- The runner locks `catalog.json.lock` using `fcntl` and updates `catalog.json` atomically via rename.
