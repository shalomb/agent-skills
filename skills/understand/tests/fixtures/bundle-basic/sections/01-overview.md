# Overview

The app starts in [the entry file](src/app.ts#L42), which reads its
settings with `parseConfig`.

```mermaid
flowchart LR
  A[app.ts] --> B[config.ts]
```
