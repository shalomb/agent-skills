---
name: pdf
description: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs.
license: Proprietary
---

# PDF Processing Skill

This skill allows you to process PDF files using Python libraries like `pypdf`, `pdfplumber`, `PyMuPDF`, and `pytesseract`.

## Usage Instructions

This skill requires specific boilerplate and code execution. **DO NOT GUESS PYTHON BOILERPLATE FOR PDF LIBRARIES.**

1. Whenever you need to process a PDF (e.g. merge, split, extract text/tables, read metadata, add watermarks, fill forms, or perform OCR), you must first read the detailed reference documentation to see the exact library syntax:
   - Use the `read` tool on `references/pdf-reference.md`.
   
2. Based on the documentation, write a single-purpose Python script to perform the task. Or, check if there are pre-built scripts in the `scripts/` directory that you can use.

3. To handle dependencies, use the `uvx` package runner as it eliminates boilerplate. For example:
   ```bash
   uvx --from pypdf python your_script.py
   uvx --from pdfplumber python extract_tables.py
   ```

By following the reference guide, you will avoid syntax errors and handle edge cases correctly.
