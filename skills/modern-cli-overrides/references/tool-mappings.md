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

## Text Replacement: `sg` (ast-grep)

Standard regex replacements via `sed` are error-prone and dangerous for code refactoring. For codebase-wide structural refactoring, prefer `sg` (ast-grep).

*Note: For complex refactoring across multiple files, prefer `ast-grep` (`sg run -p 'pattern' -r 'replacement'`).*

## JSON Processing: `grep`/`awk` → `jq`

Never use `grep`, `sed`, or `awk` to parse JSON. Always use `jq`.

| Traditional | Modern `jq` | Description |
|---|---|---|
| `grep '"name":' file.json` | `jq '.name' file.json` | Extract top-level field |
| `cat file.json \| python -m json.tool` | `jq '.' file.json` | Pretty-print JSON |

## YAML Processing: `grep`/`awk` → `yq`

Never use `grep`, `sed`, or `awk` to parse YAML. Always use `yq`.

| Traditional | Modern `yq` | Description |
|---|---|---|
| `grep 'name:' file.yaml` | `yq '.name' file.yaml` | Extract top-level field |
| `cat file.yaml` | `yq '.' file.yaml` | Pretty-print YAML |

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
