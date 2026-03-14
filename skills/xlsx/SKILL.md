---
name: xlsx
description: Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to open, read, edit, fix, or create a .xlsx, .xlsm, .csv, or .tsv file. Includes adding columns, computing formulas, formatting, charting, and cleaning messy data.
license: Proprietary
---

# Spreadsheet Processing Skill (XLSX, CSV, TSV)

This skill provides guidelines and tools for processing, editing, and creating spreadsheet files, particularly focusing on professional formatting and financial modeling standards.

## Usage Instructions

Working with spreadsheets programmatically requires adhering to specific professional standards and utilizing the right libraries. **DO NOT GUESS COLOR CODING, FORMULA APPROACHES, OR BOILERPLATE.**

1. Whenever you need to process an Excel file (.xlsx, .xlsm) or tabular data (.csv, .tsv), you must first read the detailed reference documentation to ensure you follow the required standards:
   - Use the `read` tool to load `references/xlsx-reference.md`.
   
2. The reference file contains instructions for:
   - Strict color coding standards for financial models (Blue vs Black vs Red vs Green).
   - Guidelines for delivering files with zero formula errors.
   - Code snippets and approaches for modifying workbooks using Python libraries like `openpyxl` or `pandas`.

3. Always execute small scripts using a package runner (e.g. `uvx --from openpyxl python script.py`) based on the reference guide rather than guessing the library API. Check the `scripts/` directory for any pre-existing helper scripts.
