---
name: software-design-principles
description: Capture, catalogue, and retrieve software design principles discovered during coding sessions. Use this skill when the user asks to "capture a design principle", "remember this principle", "what principles do we have", or "apply our design principles".
---

# Software Design Principles

## Overview
This skill allows you to capture and retrieve software design principles discovered during coding sessions. By cataloging these principles (like the DWIM - "Do What I Mean" pattern), you can build a repository of context-specific architectural and UX patterns that can be re-applied to future problems.

## Workflows

### 1. Capturing a New Principle
When the user asks to capture or remember a newly discovered design principle:
1. Identify the core concept, context, and the problem it solves.
2. Read the existing catalogue in `references/index.md` to ensure no duplicates.
3. Create a new markdown file in `references/principles/<kebab-case-name>.md` with:
   - **Context/Problem**
   - **Solution/Pattern**
   - **Example** (Use the exact coding context where it was discovered)
4. Append a link and a one-sentence summary to `references/index.md`.
5. Confirm with the user that the principle has been saved and summarize it briefly.

### 2. Retrieving and Applying Principles
When you are about to make an architectural decision, or the user asks what principles we have:
1. Read `references/index.md` to load the current registry into your context.
2. If a principle seems relevant, read its specific `references/principles/<name>.md` file.
3. Suggest the relevant principle(s) based on the user's current task.
4. Apply the principle directly to the code you are writing.

## Reference Materials
- [index.md](references/index.md): The lightweight registry of all captured software design principles.
- `references/principles/`: Directory containing detailed files for each principle.
