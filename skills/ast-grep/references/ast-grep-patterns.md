# ast-grep Pattern Examples by Language

## Python

```bash
# All function definitions
sg run -p 'def $FUNC($$$):' -l python .

# Async functions only  
sg run -p 'async def $FUNC($$$):' -l python .

# Function calls
sg run -p '$OBJ.$METHOD($$$ARGS)' -l python .

# Import statements
sg run -p 'import $MOD' -l python .
sg run -p 'from $MOD import $NAME' -l python .

# Class definitions
sg run -p 'class $NAME($$$BASES):' -l python .

# Specific decorator usage
sg run -p '@$DECORATOR
def $FUNC($$$):' -l python .

# Exception handling
sg run -p 'except $EXC as $VAR:' -l python .

# Extract all function names via JSON
sg run -p 'def $FUNC($$$):' -l python . --json=stream | \
  python3 -c "
import json,sys
for l in sys.stdin:
    m=json.loads(l)
    print(m['file'] + ':' + str(m['range']['start']['line']+1) + ': ' +
          m['metaVariables']['single']['FUNC']['text'])
"
```

## JavaScript / TypeScript

```bash
# console.log calls
sg run -p 'console.log($$$)' -l js .

# Arrow functions
sg run -p '($$$ARGS) => $BODY' -l ts .

# React hooks
sg run -p 'useState($INIT)' -l tsx .
sg run -p 'useEffect($CB, $DEPS)' -l tsx .

# async/await
sg run -p 'await $EXPR' -l ts .

# Import statements
sg run -p 'import $DEFAULT from "$MOD"' -l ts .
sg run -p 'import { $$$NAMES } from "$MOD"' -l ts .

# Rewrite: var → const
sg run -p 'var $V = $E' -r 'const $V = $E' -l js . --update-all

# Rewrite: old API to new
sg run -p 'Promise.resolve($V).then($CB)' \
       -r 'Promise.resolve($V).then($CB)' -l js .
```

## Go

```bash
# Function declarations
sg run -p 'func $FUNC($$$PARAMS) $$$RET {$$$BODY}' -l go .

# Method declarations
sg run -p 'func ($RECV $TYPE) $METHOD($$$) $$$RET {$$$}' -l go .

# Error checks
sg run -p 'if err != nil { $$$BODY }' -l go .

# fmt.Println / log calls  
sg run -p 'fmt.Println($$$)' -l go .
sg run -p 'log.Printf($$$)' -l go .

# Struct fields
sg run -p 'type $NAME struct { $$$FIELDS }' -l go .
```

## Rust

```bash
# Function definitions
sg run -p 'fn $FUNC($$$) $$$RET { $$$BODY }' -l rust .

# unwrap() calls (risky pattern)
sg run -p '$EXPR.unwrap()' -l rust .

# expect() calls
sg run -p '$EXPR.expect($MSG)' -l rust .

# impl blocks
sg run -p 'impl $TYPE { $$$METHODS }' -l rust .

# use statements
sg run -p 'use $PATH;' -l rust .
```

## Metavariable extraction recipe

```python
import subprocess, json

def sg_extract(pattern, lang, path, var_names):
    """Run sg and extract named metavariables as structured records."""
    result = subprocess.run(
        ['sg', 'run', '-p', pattern, '-l', lang, '--json=stream', path],
        capture_output=True, text=True
    )
    records = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        sv = m['metaVariables']['single']
        mv = m['metaVariables']['multi']
        record = {
            'file': m['file'],
            'line': m['range']['start']['line'] + 1,
        }
        for v in var_names:
            if v in sv:
                record[v] = sv[v]['text']
            elif v in mv:
                record[v] = [x['text'] for x in mv[v]]
        records.append(record)
    return records

# Example: extract all Python function names and their files
funcs = sg_extract('def $FUNC($$$):', 'python', '.', ['FUNC'])
for f in funcs:
    print(f"{f['file']}:{f['line']} — {f['FUNC']}")
```

## Inline rule for linting

```yaml
# no-print-statements.yml
id: no-print-statements
language: python
rule:
  pattern: print($$$)
message: Remove debug print statement
severity: warning
```

```bash
sg scan -r no-print-statements.yml src/
sg scan -r no-print-statements.yml src/ --json=stream  # for CI
```

## Composing rules with `all` / `any` / `not`

```yaml
# Function that has a docstring AND calls super()
id: must-call-super
language: python
rule:
  all:
    - pattern: 'def __init__($$$): $$$'
    - has:
        pattern: 'super().__init__($$$)'
        stopBy: end
```

## Node kind matching

When pattern isn't precise enough, match by AST node type:

```bash
# Find all string literals
sg run --pattern '$S' --selector string -l python .

# Find all binary expressions
sg run --pattern '$A + $B' -l python .
```

Use `sg run -p 'YOUR_PATTERN' -l LANG --debug-query=ast` to inspect what AST nodes your pattern produces.
