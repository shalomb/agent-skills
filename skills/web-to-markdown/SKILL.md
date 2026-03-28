---
name: web-to-markdown
version: 1.1.0
description: |
  Convert URLs or local files (PDF/DOCX/PPTX/HTML) to Markdown, with optional
  summarization. Single or batch processing. Uses markitdown for intelligent
  extraction, falls back to curl+pandoc. Use when fetching web pages as
  markdown, converting documents for analysis, or producing quick summaries.
---

# Web to Markdown

Convert URLs and local files to Markdown for analysis, quoting, or processing.
Optionally summarize long documents before deeper work.

## Quick Usage

### Convert a URL or file

```bash
uvx --from 'markitdown[pdf]' markitdown <url-or-path>
```

Save to a specific file:

```bash
uvx --from 'markitdown[pdf]' markitdown <url-or-path> > /tmp/doc.md
```

### Convert + summarize

Use the wrapper script for summarization with context:

```bash
node scripts/to-markdown.mjs <url-or-path> --summary --prompt "Focus on security implications"
node scripts/to-markdown.mjs <url-or-path> --tmp     # write to temp file, print path
node scripts/to-markdown.mjs <url-or-path> --out notes.md
```

The summarizer:
1. Converts to Markdown via `markitdown`
2. Saves full Markdown to a temp file (prints path as hint)
3. Runs `pi --model claude-haiku-4-5` to summarize with your prompt

**Always provide context** — summaries without a focus prompt are generic and unhelpful.

### Batch processing (shell function)

Add to `.bashrc` / `.zshrc`:

```bash
web-to-markdown() {
  local url output_dir format batch_file output_file
  output_dir="." format="markdown"

  while [[ $# -gt 0 ]]; do
    case $1 in
      --batch) batch_file="$2"; shift 2 ;;
      --output-dir) output_dir="$2"; shift 2 ;;
      --format) format="$2"; shift 2 ;;
      --output) output_file="$2"; shift 2 ;;
      *) url="$1"; shift ;;
    esac
  done

  _fetch() {
    local u=$1 fmt=$2
    local content
    content=$(uvx --from 'markitdown[pdf]' markitdown "$u" 2>/dev/null) \
      || content=$(curl -sL "$u" | pandoc -f html -t markdown)
    [[ -z "$content" ]] && return 1
    [[ "$fmt" == "plain" ]] && echo "$content" | pandoc -f markdown -t plain || echo "$content"
  }

  if [[ -n "${batch_file-}" ]]; then
    [[ ! -f "$batch_file" ]] && { echo "ERROR: $batch_file not found" >&2; return 1; }
    mkdir -p "$output_dir"
    local ok=0 fail=0
    while IFS= read -r u || [[ -n "$u" ]]; do
      [[ -z "$u" || "$u" =~ ^# ]] && continue
      local name ext out
      name=$(echo "$u" | sed 's|https\?://||;s|/|-|g' | cut -c1-100)
      ext=$([[ "$format" == "plain" ]] && echo txt || echo md)
      out="$output_dir/${name}.${ext}"
      if _fetch "$u" "$format" > "$out" 2>/dev/null; then
        echo "✓ $(basename "$out")" >&2; (( ++ok ))
      else
        echo "✗ $u" >&2; rm -f "$out"; (( ++fail ))
      fi
    done < "$batch_file"
    echo "Done: $ok ok, $fail failed" >&2
    return $(( fail > 0 ? 1 : 0 ))
  fi

  [[ -z "${url-}" ]] && { echo "Usage: web-to-markdown <URL> [--output FILE] [--format markdown|plain]" >&2; return 1; }
  [[ -z "${output_file-}" ]] && {
    local name ext
    name=$(echo "$url" | sed 's|https\?://||;s|/|-|g' | cut -c1-100)
    ext=$([[ "$format" == "plain" ]] && echo txt || echo md)
    output_file="${name}.${ext}"
  }
  _fetch "$url" "$format" > "$output_file" && echo "✓ Saved: $output_file" || { rm -f "$output_file"; return 1; }
}
```

**Examples:**
```bash
web-to-markdown "https://example.com/article" --output article.md
web-to-markdown --batch urls.txt --output-dir ./docs --format markdown
web-to-markdown "https://example.com" --format plain
```

## Dependencies

- `markitdown` (auto-installed via `uvx`) — smart content extraction
- `curl` + `pandoc` — fallback for when markitdown fails
- `pi` — only needed for `--summary` mode
