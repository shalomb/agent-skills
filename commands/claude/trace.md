---
description: Trace bugs and refactoring blast radius by chaining Codemap, LSP, and AST-grep
---

You are tasked with: Trace bugs and refactoring blast radius by chaining Codemap, LSP, and AST-grep.

Follow the instructions in the `macro-to-micro` skill:
1. Follow the 3-tier articulation chain: Macro (Codemap file graph) -> Meso (LSP symbol graph) -> Micro (AST-grep syntax tree).
2. Identify hub files and dependency blast radius with Codemap before editing.
3. Trace call chains and data flow with LSP (`lsp reference`, `lsp definition`, `lsp outline`).
4. Perform surgical syntax-aware transformations using AST-grep (`sg run`).

User request:
$ARGUMENTS
