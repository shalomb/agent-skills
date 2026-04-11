# Editing Existing DOCX Documents

This reference provides detailed instructions for modifying existing .docx files by manipulating their underlying XML.

## Editing Workflow

Follow all 3 steps in order:

### Step 1: Unpack
```bash
python scripts/office/unpack.py document.docx unpacked/
```
Extracts XML, pretty-prints, merges adjacent runs, and converts smart quotes to XML entities.

### Step 2: Edit XML
Edit files in `unpacked/word/` (primarily `document.xml`).

- **Tracked Changes**: Use `Claude` as the author unless requested otherwise.
- **Smart Quotes**: Use XML entities (`&#x2018;`, `&#x2019;`, `&#x201C;`, `&#x201D;`).
- **Comments**: Use `scripts/comment.py` to handle boilerplate.
  ```bash
  python scripts/comment.py unpacked/ 0 "Comment text"
  ```

### Step 3: Pack
```bash
python scripts/office/pack.py unpacked/ output.docx --original document.docx
```
Validates with auto-repair, condenses XML, and creates DOCX.

---

## XML Reference

### Tracked Changes
**Insertion:**
```xml
<w:ins w:id="1" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:t>inserted text</w:t></w:r>
</w:ins>
```

**Deletion:**
```xml
<w:del w:id="2" w:author="Claude" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
```

**Deleting Paragraphs**: Mark the paragraph mark as deleted inside `<w:pPr><w:rPr>`.
```xml
<w:pPr><w:rPr><w:del w:id="1" w:author="Claude" w:date="..."/></w:rPr></w:pPr>
```

### Comments
**CRITICAL: Markers are siblings of `<w:r>`, never inside.**
```xml
<w:commentRangeStart w:id="0"/>
<w:r><w:t>commented text</w:t></w:r>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>
```

### Images
1. Add image to `word/media/`.
2. Add relationship to `word/_rels/document.xml.rels`.
3. Add content type to `[Content_Types].xml`.
4. Reference with `<w:drawing>` in `document.xml`.

### Schema Compliance
- **Element order in `<w:pPr>`**: `<w:pStyle>`, `<w:numPr>`, `<w:spacing>`, `<w:ind>`, `<w:jc>`, `<w:rPr>` last.
- **Whitespace**: Add `xml:space="preserve"` to `<w:t>` with leading/trailing spaces.
- **RSIDs**: Must be 8-digit hex (e.g., `00AB1234`).
