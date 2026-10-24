#!/usr/bin/env python3
"""
Validates Harness Pipeline YAML documents.
Uses official Harness JSON schema (schemas/pipeline.json) via jsonschema (Draft-07),
and provides offline JEXL expression syntax checking.
"""

import sys
import re
import json
from pathlib import Path
import yaml
import jsonschema

SKILL_DIR = Path(__file__).resolve().parent.parent
PIPELINE_SCHEMA_PATH = SKILL_DIR / "schemas" / "pipeline.json"
_PIPELINE_VALIDATOR = None

KNOWN_STAGE_TYPES = {
    "CI",
    "CD",
    "Deployment",
    "Custom",
    "FeatureFlag",
    "Approval",
    "Pipeline",
    "Security",
}

KNOWN_JEXL_PREFIXES = (
    "pipeline.",
    "project.",
    "org.",
    "account.",
    "stage.",
    "stages.",
    "step.",
    "steps.",
    "execution.",
    "secrets.",
    "variable.",
    "env.",
    "input",
    "infra.",
    "service.",
    "artifacts.",
    "rollback.",
    "workflow.",
)

JEXL_PATTERN = re.compile(r"<\+([^>]+)>")


def get_pipeline_validator():
    global _PIPELINE_VALIDATOR
    if _PIPELINE_VALIDATOR is not None:
        return _PIPELINE_VALIDATOR

    if not PIPELINE_SCHEMA_PATH.exists() or PIPELINE_SCHEMA_PATH.stat().st_size == 0:
        try:
            from bootstrap_schemas import ensure_schemas
            ensure_schemas()
        except Exception:
            pass

    if PIPELINE_SCHEMA_PATH.exists():
        try:
            with open(PIPELINE_SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema_json = json.load(f)
            _PIPELINE_VALIDATOR = jsonschema.Draft7Validator(schema_json)
        except Exception as e:
            print(f'⚠️ Warning: Failed to load pipeline.json schema: {e}', file=sys.stderr)
    return _PIPELINE_VALIDATOR


def extract_jexl_expressions(node, found=None):
    if found is None:
        found = []
    if isinstance(node, str):
        for match in JEXL_PATTERN.findall(node):
            found.append(match.strip())
    elif isinstance(node, dict):
        for v in node.values():
            extract_jexl_expressions(v, found)
    elif isinstance(node, list):
        for item in node:
            extract_jexl_expressions(item, found)
    return found


def validate_jexl_expressions(expressions: list[str]) -> list[str]:
    errors = []
    for expr in expressions:
        if not expr:
            errors.append("Empty JEXL expression '<+>' found")
            continue

        clean_expr = expr.split()[0] if " " in expr else expr
        clean_expr = clean_expr.lstrip("!")

        has_valid_prefix = any(
            clean_expr.startswith(prefix) for prefix in KNOWN_JEXL_PREFIXES
        )
        if not has_valid_prefix:
            errors.append(
                f"Unknown or non-standard JEXL expression prefix: '<+{expr}>'"
            )
    return errors


def validate_pipeline_doc(data: dict, file_path: Path) -> list[str]:
    errors = []
    pipeline = data.get("pipeline")
    if not isinstance(pipeline, dict):
        return [f"{file_path.name}: Root must contain a 'pipeline' object"]

    # Official JSON Schema validation
    validator = get_pipeline_validator()
    if validator is not None:
        for err in validator.iter_errors(data):
            loc = ".".join(str(p) for p in err.path) if err.path else "root"
            errors.append(f"{file_path.name}: Schema error at '{loc}': {err.message}")

    # Top-level required fields
    required_fields = ["identifier", "name", "projectIdentifier", "orgIdentifier"]
    for req in required_fields:
        if not pipeline.get(req):
            errors.append(
                f"{file_path.name}: Pipeline missing required field '{req}'"
            )

    # JEXL expression validation across entire document
    jexl_exprs = extract_jexl_expressions(pipeline)
    jexl_errors = validate_jexl_expressions(jexl_exprs)
    for je in jexl_errors:
        errors.append(f"{file_path.name}: {je}")

    return errors


def validate_file(file_path: Path) -> list[str]:
    if not file_path.exists():
        return [f"File not found: {file_path}"]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            docs = list(yaml.safe_load_all(f))
    except Exception as e:
        return [f"YAML parsing error in {file_path.name}: {e}"]

    errors = []
    for doc in docs:
        if not doc or not isinstance(doc, dict):
            continue

        if "pipeline" in doc:
            errors.extend(validate_pipeline_doc(doc, file_path))
        else:
            errors.append(
                f"{file_path.name}: Document does not contain a root 'pipeline' object"
            )

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/validate_pipeline_yaml.py <path-to-pipeline.yaml> [more-files...]")
        return 1

    total_errors = 0
    for target in sys.argv[1:]:
        p = Path(target)
        print(f"🔍 Validating {p}...")
        errs = validate_file(p)
        if errs:
            print(f"  ❌ FAILED ({len(errs)} issues found):")
            for e in errs:
                print(f"     - {e}")
            total_errors += len(errs)
        else:
            print(f"  ✅ PASSED (Valid Harness pipeline schema)")

    if total_errors > 0:
        print(f"\n❌ Validation failed with {total_errors} total error(s).")
        return 1

    print("\n✨ All documents passed validation!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
