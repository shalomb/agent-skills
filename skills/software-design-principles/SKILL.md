---
name: software-design-principles
description: Capture, catalogue, and retrieve software design principles discovered during coding sessions. Use this skill when the user asks to "capture a design principle", "remember this principle", "what principles do we have", or "apply our design principles".
---

# Software Design Principles

## Overview
This skill allows you to capture and retrieve software design principles discovered during coding sessions. By cataloging these principles, you build a repository of context-agnostic architectural and UX patterns that can be re-applied across different domains, languages, and frameworks.

## Workflows

### 1. Capturing a New Principle
When the user asks to capture or remember a newly discovered design principle:
1. Formulate an **Abstract Problem** and **Abstract Solution** that are entirely domain-agnostic (no specific languages or frameworks).
2. Document the exact context where it was discovered under **Concrete Examples**.
3. Identify relevant **Tags** (e.g., UX, Architecture, Refactoring) and **Related Principles** for cross-referencing.
4. Create a new markdown file in `references/<principle-name>.md` using the standard format.
5. Add an entry to the **Principles Index** below in this `SKILL.md` file with a 1-sentence summary and a link to the new file.
6. Commit the changes to the `~/.gemini/skills` git repository.

### 2. Retrieving and Applying Principles
When you are about to make an architectural decision, or the user asks what principles we have:
1. Review the **Principles Index** below.
2. Use the `view_file` tool to read the specific reference file(s) that seem relevant to your current task (Progressive Disclosure).
3. Apply the principle directly to the code you are writing.

---

## Principles Index

*Read the specific file using `view_file` when you need the full context or concrete examples of a principle.*

- **[DWIM (Do What I Mean)](references/dwim.md):** The system should intrinsically handle hidden dependencies and boilerplate configuration, providing a 'pit of success' without forcing explicit orchestration by the user.
