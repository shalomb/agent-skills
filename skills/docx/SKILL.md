---
name: docx
description: Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Includes extracting, reorganizing, and formatting content for professional documents.
license: Proprietary
---

# DOCX Creation, Editing, and Analysis Skill

This skill allows you to process Word documents (.docx files) using command-line tools and scripting libraries like `pandoc` or `docx-js`.

## Usage Instructions

Working with .docx files (which are zipped XML archives) requires specific tools and approaches. **DO NOT GUESS THE XML STRUCTURE OR BOILERPLATE CODE.**

1. Whenever you need to create, edit, or analyze a DOCX file, you must first read the detailed reference documentation to see the exact approaches and tools available:
   - Use the `read` tool on `references/docx-reference.md`.
   
2. The reference file contains instructions for:
   - Reading/analyzing content (using `pandoc` or raw XML extraction).
   - Creating new documents (using Node.js `docx` package).
   - Editing existing documents (unpacking, modifying XML, repacking).
   - Converting legacy `.doc` files to `.docx`.

3. Always execute small, single-purpose scripts based on the reference guide rather than writing large blocks of code from memory. Check the `scripts/` directory for existing tools before writing your own.
