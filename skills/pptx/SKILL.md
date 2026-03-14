---
name: pptx
description: Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes creating slide decks, reading/parsing, extracting text, editing, modifying, updating existing presentations, combining or splitting slide files, and working with templates, layouts, speaker notes, or comments.
license: Proprietary
---

# PPTX Skill

This skill allows you to process PowerPoint (.pptx) files using command-line tools and scripting libraries like `python-pptx` or `pptxgenjs`.

## Usage Instructions

This skill requires specific boilerplate and code execution. **DO NOT GUESS BOILERPLATE FOR SLIDE GENERATION.**

1. Whenever you need to process a PPTX file, you must first read the detailed reference documentation to see the exact library syntax and scripts available:
   - Use the `read` tool on `references/pptx-reference.md`.
   
2. The reference file contains instructions for:
   - Reading/analyzing content (using tools like `markitdown`).
   - Editing or creating from templates using Python (`python-pptx`).
   - Creating presentations from scratch (using JavaScript/Node.js or Python).

3. Always execute small, single-purpose scripts rather than writing large blocks of code from memory. Check the `scripts/` directory for existing tools before writing your own.
