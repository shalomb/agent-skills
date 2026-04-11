---
name: docx
description: "Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of \"Word doc\", \"word document\", \".docx\", or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx files, inserting or replacing images in documents, performing find-and-replace in Word files, working with tracked changes or comments, or converting content into a polished Word document. If the user asks for a \"report\", \"memo\", \"letter\", \"template\", or similar deliverable as a Word or .docx file, use this skill. Do NOT use for PDFs, spreadsheets, Google Docs, or general coding tasks unrelated to document generation."
license: Proprietary. LICENSE.txt has complete terms
---

# DOCX creation, editing, and analysis

## Overview

A .docx file is a ZIP archive containing XML files.

## Task Quick Start

| Task | Approach |
|------|----------|
| **Analyze content** | `pandoc document.docx -o output.md` |
| **Convert .doc** | `python scripts/office/soffice.py --convert-to docx document.doc` |
| **Create new doc** | Use `docx-js`. See [references/creating.md](references/creating.md) |
| **Edit existing doc** | Unpack → edit XML → repack. See [references/editing.md](references/editing.md) |
| **Clean changes** | `python scripts/accept_changes.py input.docx output.docx` |
| **Convert to PDF** | `python scripts/office/soffice.py --convert-to pdf document.docx` |

## Reference Materials

To ensure high-quality document manipulation, refer to these detailed guides:

- **Creating Documents**: [references/creating.md](references/creating.md) - Full guide for `docx-js` (JavaScript).
- **Editing Documents**: [references/editing.md](references/editing.md) - Detailed workflow for unpacking and editing XML directly.
- **XML Reference**: [references/editing.md#xml-reference](references/editing.md#xml-reference) - Patterns for tracked changes, comments, and images.

## Critical Rules

### For docx-js (Creating)
- **Set page size explicitly** - Defaults to A4; use US Letter (12240 x 15840 DXA) for US documents.
- **Tables need dual widths** - `columnWidths` array AND cell `width`, both must match in DXA.
- **Never use `\n` or unicode bullets** - Use separate Paragraphs and `LevelFormat.BULLET`.

### For XML Editing (Modifying)
- **Author Identity**: Use "Claude" for tracked changes and comments.
- **Minimal edits** - Only mark what actually changes in the XML.
- **Comment Markers**: Siblings of `<w:r>`, never inside.

## Dependencies

- **pandoc**: Text extraction
- **docx**: `npm install -g docx` (new documents)
- **LibreOffice**: PDF conversion (`scripts/office/soffice.py`)
- **Poppler**: `pdftoppm` for images
