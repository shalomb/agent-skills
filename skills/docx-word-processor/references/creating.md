# Creating New DOCX Documents

This reference provides detailed instructions and code patterns for generating .docx files using the `docx-js` library.

## Setup
Install the library: `npm install -g docx`

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
        Header, Footer, AlignmentType, PageOrientation, LevelFormat, ExternalHyperlink,
        TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
        VerticalAlign, PageNumber, PageBreak } = require('docx');

const doc = new Document({ sections: [{ children: [/* content */] }] });
Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer));
```

## Page Size
**CRITICAL: docx-js defaults to A4, not US Letter.** Always set page size explicitly.

```javascript
sections: [{
  properties: {
    page: {
      size: {
        width: 12240,   // 8.5 inches in DXA (1440 DXA = 1 inch)
        height: 15840   // 11 inches in DXA
      },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
    }
  },
  children: [/* content */]
}]
```

## Styles
Use Arial as the default font. Use exact IDs to override built-in styles.

```javascript
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
    ]
  }
});
```

## Lists
**NEVER use unicode bullets.** Use numbering config with `LevelFormat.BULLET`.

```javascript
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  }
});
```

## Tables
**CRITICAL: Tables need dual widths.** Set `columnWidths` on the table AND `width` on each cell using `WidthType.DXA`.

```javascript
new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [4680, 4680],
  rows: [
    new TableRow({
      children: [
        new TableCell({
          width: { size: 4680, type: WidthType.DXA },
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
          children: [new Paragraph({ children: [new TextRun("Cell")] })]
        })
      ]
    })
  ]
})
```

## Images
**CRITICAL: type parameter is REQUIRED.**

```javascript
new ImageRun({
  type: "png",
  data: fs.readFileSync("image.png"),
  transformation: { width: 200, height: 150 },
  altText: { title: "Title", description: "Desc", name: "Name" }
})
```

## Critical Rules Summary
- Set page size explicitly (US Letter is 12240x15840 DXA).
- Landscape: pass portrait dimensions and set `orientation: LANDSCAPE`.
- Never use `\n` or unicode bullets.
- PageBreak must be inside a Paragraph.
- Tables: Always use `WidthType.DXA`, sum of `columnWidths` must equal table width.
- Use `ShadingType.CLEAR` for table shading.
- TOC requires `HeadingLevel` and `outlineLevel` in styles.
