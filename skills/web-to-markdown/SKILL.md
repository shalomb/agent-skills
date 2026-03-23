---
name: web-to-markdown
version: 1.0.0
description: |
  Convert URLs to markdown or plain text. Single or batch processing. Uses markitdown
  for intelligent extraction, falls back to curl+pandoc. Include in .bashrc or use
  directly. Great for research, reference capture, and ADR workflows.
---

# Web to Markdown

Quick utility to fetch web pages as markdown or plain text. Single URLs or batch process files.

## Setup

Add this function to your `.bashrc`, `.zshrc`, or shell profile:

```bash
web-to-markdown() {
  local url output_dir format batch_file output_file
  output_dir="." && format="markdown"
  
  while [[ $# -gt 0 ]]; do
    case $1 in
      --batch) batch_file="$2"; shift 2 ;;
      --output-dir) output_dir="$2"; shift 2 ;;
      --format) format="$2"; shift 2 ;;
      --output) output_file="$2"; shift 2 ;;
      *) url="$1"; shift ;;
    esac
  done
  
  local _fetch_url() {
    local u="$1" fmt="$2"
    echo "Fetching: $u" >&2
    local content
    content=$(uvx markitdown "$u" 2>/dev/null) || content=$(curl -sL "$u" | pandoc -f html -t markdown)
    [[ -z "$content" ]] && { echo "ERROR: Failed to fetch $u" >&2; return 1; }
    [[ "$fmt" == "plain" ]] && echo "$content" | pandoc -f markdown -t plain || echo "$content"
  }
  
  if [[ -n "$batch_file" ]]; then
    [[ ! -f "$batch_file" ]] && { echo "ERROR: File not found: $batch_file" >&2; return 1; }
    mkdir -p "$output_dir"
    local success_count=0 fail_count=0
    while IFS= read -r u || [[ -n "$u" ]]; do
      [[ -z "$u" || "$u" =~ ^# ]] && continue
      local filename=$(echo "$u" | sed 's|https\?://||' | sed 's|/|-|g' | cut -c1-100)
      local ext=$([[ "$format" == "plain" ]] && echo "txt" || echo "md")
      local outfile="$output_dir/${filename}.${ext}"
      if _fetch_url "$u" "$format" > "$outfile" 2>/dev/null; then
        echo "✓ $(basename "$outfile")" >&2
        ((success_count++))
      else
        echo "✗ $u" >&2
        rm -f "$outfile"
        ((fail_count++))
      fi
    done < "$batch_file"
    echo "Summary: $success_count ok, $fail_count failed" >&2
    return $(( fail_count > 0 ? 1 : 0 ))
  fi
  
  [[ -z "$url" ]] && { echo "Usage: web-to-markdown <URL> [--output FILE] [--format markdown|plain]" >&2; return 1; }
  [[ -z "$output_file" ]] && output_file=$(echo "$url" | sed 's|https\?://||' | sed 's|/|-|g' | cut -c1-100).$([[ "$format" == "plain" ]] && echo "txt" || echo "md")
  if _fetch_url "$url" "$format" > "$output_file"; then
    echo "✓ Saved: $output_file"
    return 0
  else
    rm -f "$output_file"
    return 1
  fi
}
```

Then reload: `source ~/.bashrc` (or your shell profile).

---

## Usage

**Single URL:**
```bash
web-to-markdown "https://example.com/article" --output article.md
web-to-markdown "https://example.com/article" --format plain  # auto-names file
```

**Batch process:**
```bash
# Create a file with URLs (one per line, # for comments)
cat > urls.txt << 'EOF'
https://github.com/blader/humanizer
https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
# Skip this one for now
# https://example.com/big-doc
EOF

# Fetch all as markdown
web-to-markdown --batch urls.txt --output-dir ./docs --format markdown

# Or as plain text for searching
web-to-markdown --batch urls.txt --output-dir ./research --format plain
```

---

## Format Choice

| Format | Use when | Output |
|--------|----------|--------|
| `markdown` (default) | Need links, formatting, publishing | `.md` files |
| `plain` | Researching, grep/search, analysis | `.txt` files |

---

<details>
<summary><strong>Advanced: How it works, options, and examples</strong></summary>

## How It Works

1. **Fetch**: `curl -sL` gets the HTML
2. **Extract**: Try `markitdown` (smart content extraction), fallback to `pandoc -f html`
3. **Convert**: Plain text via `pandoc -f markdown -t plain` if requested
4. **Save**: Write to file (auto-generated or specified name)

## Options

| Option | Value | Default |
|--------|-------|---------|
| `--output FILE` | Output filename | Auto-generated from URL |
| `--output-dir DIR` | Directory for batch output | Current directory `.` |
| `--format` | `markdown` or `plain` | `markdown` |
| `--batch FILE` | File with URLs (one per line) | Single URL mode |

## Examples

### Research collection (plain text)
```bash
web-to-markdown --batch research.txt --output-dir ./research --format plain
grep -r "architecture" ./research/ | head -10
```

### Documentation capture with markdown
```bash
cat > refs.txt << 'EOF'
https://github.com/blader/humanizer
https://docs.github.com/en/actions
https://www.terraform.io/docs
EOF

web-to-markdown --batch refs.txt --output-dir ./docs --format markdown
ls -lh ./docs/
```

### Filter and process by domain
```bash
grep "github.com" urls.txt > github-urls.txt
web-to-markdown --batch github-urls.txt --output-dir ./github
```

### For ADR reference material
```bash
# Batch fetch references for an architectural decision
cat > adr-refs.txt << 'EOF'
https://www.terraform.io/docs/language/resources
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/
EOF

web-to-markdown --batch adr-refs.txt --output-dir ./adr-research --format markdown
```

## Limitations

- **JavaScript**: Fetches HTML only, not JS-rendered content
- **Auth**: No support for login-required pages
- **Rate limiting**: No backoff (add `sleep 1` if needed)
- **Large files**: Very long pages may exceed pandoc limits

## Dependencies

Required:
- `curl` (pre-installed on most systems)
- `bash` 4.0+

Optional but recommended:
- `markitdown` (auto-installed via `uvx`, better extraction)
- `pandoc` (auto-installed via `uvx`)

Manual install:
```bash
brew install curl pandoc  # macOS
sudo apt install curl pandoc python3-pip && pip install markitdown  # Linux
```

</details>

---

**Last Updated**: 2026-03-23
