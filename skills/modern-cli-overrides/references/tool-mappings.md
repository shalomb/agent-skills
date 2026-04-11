# Modern CLI Tool Mappings

This reference provides the translations and flags for converting traditional POSIX coreutils to their modern Rust/Go equivalents.

## File Search: `find` → `fd`

`fd` is a simple, fast, and user-friendly alternative to `find`. It respects `.gitignore` by default and uses regex for patterns.

| Traditional `find` | Modern `fd` | Description |
|---|---|---|
| `find . -name "*.py"` | `fd -e py` | Find files by extension |
| `find . -type d -name "src"` | `fd -t d src` | Find directories named "src" |
| `find . -iname "*test*"` | `fd -i test` | Case-insensitive search |
| `find . -name "foo" -exec rm {} \;` | `fd foo -X rm` | Execute command on results (batch) |
| `find . -name "foo" -exec rm {} +` | `fd foo -x rm` | Execute command on results (per file) |
| `find . -path "*/node_modules/*"` | `fd -u "pattern"` | Unrestricted search (ignore `.gitignore`) |

## Text Search: `grep` → `rg` (ripgrep)

`rg` is dramatically faster than `grep`, automatically respects `.gitignore`, and provides better default output.

| Traditional `grep` | Modern `rg` | Description |
|---|---|---|
| `grep -r "pattern" .` | `rg "pattern"` | Recursive search (default) |
| `grep -i "pattern" file` | `rg -i "pattern" file` | Case-insensitive search |
| `grep -v "pattern" file` | `rg -v "pattern" file` | Invert match |
| `grep -C 3 "pattern" .` | `rg -C 3 "pattern"` | Show 3 lines of context |
| `grep -r "pattern" . --include="*.py"` | `rg "pattern" -t py` | Filter by file type |
| `grep -l "pattern" .` | `rg -l "pattern"` | Print only filenames with matches |
| `grep -r "pattern" . --no-ignore` | `rg -u "pattern"` | Unrestricted (ignore `.gitignore`) |

## Text Replacement: `sed` → `sd` (or `sg`)

`sd` uses standard regex (not POSIX basic regex) and treats inputs as raw strings by default, making it much safer and easier than `sed` for code refactoring. For structural refactoring, prefer `sg` (ast-grep).

| Traditional `sed` | Modern `sd` | Description |
|---|---|---|
| `sed -i 's/old/new/g' file` | `sd 'old' 'new' file` | In-place replacement |
| `sed 's/old/new/g' file` | `sd -p 'old' 'new' file` | Preview replacement (stdout) |
| `sed -i 's/regex/new/g' file` | `sd -s 'regex' 'new' file` | Literal string replacement (no regex) |

*Note: For complex refactoring across multiple files, prefer `ast-grep` (`sg run -p 'pattern' -r 'replacement'`).*

## Listing Files: `ls` → `eza`

`eza` is a modern replacement for `ls` with better defaults, git status integration, and colors.

| Traditional `ls` | Modern `eza` | Description |
|---|---|---|
| `ls -la` | `eza -la` | List all files with details |
| `ls -R` | `eza -R` | Recurse into directories |
| `ls -la` | `eza -la --git` | Include git status columns |
| `tree` | `eza --tree` | Print as a tree |

## JSON Processing: `grep`/`awk` → `jq`

Never use `grep`, `sed`, or `awk` to parse JSON. Always use `jq`.

| Traditional | Modern `jq` | Description |
|---|---|---|
| `grep '"name":' file.json` | `jq '.name' file.json` | Extract top-level field |
| `cat file.json \| python -m json.tool` | `jq '.' file.json` | Pretty-print JSON |

## API Testing: `curl` → `httpie` (`http`)

`curl` is powerful but its syntax can be arcane for JSON payloads. `httpie` is designed for human readability, offering intuitive syntax and automatic JSON serialization.

| Traditional `curl` | Modern `httpie` (`http`) | Description |
|---|---|---|
| `curl api.com` | `http api.com` | Simple GET request |
| `curl -X POST api.com` | `http POST api.com` | Simple POST request |
| `curl -H "Authorization: Bearer token" api.com` | `http api.com "Authorization: Bearer token"` | Pass HTTP headers |
| `curl -H "Content-Type: application/json" -d '{"name":"admin"}' api.com` | `http POST api.com name=admin` | Send JSON payload |
| `curl -d "name=admin" -X POST api.com` | `http -f POST api.com name=admin` | Send Form data |
| `curl -O https://example.com/file.zip` | `http -d https://example.com/file.zip` | Download a file |
