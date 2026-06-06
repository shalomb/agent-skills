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
2. Read the existing catalogue in `references/principles.md` to ensure no duplicates.
3. Append the new principle to `references/principles.md` using the standard format:
   - **Principle Name**
   - **Context/Problem**
   - **Solution/Pattern**
   - **Example** (Use the exact coding context where it was discovered)
4. Confirm with the user that the principle has been saved and summarize it briefly.

### 2. Retrieving and Applying Principles
When you are about to make an architectural decision, or the user asks what principles we have:
1. Read `references/principles.md` to load the current catalogue into your context.
2. Suggest the relevant principle(s) based on the user's current task.
3. Apply the principle directly to the code you are writing.

## Reference Materials
- [principles.md](references/principles.md): The living catalogue of all captured software design principles.
