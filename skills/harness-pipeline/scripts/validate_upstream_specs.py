#!/usr/bin/env python3
"""
Validates downloaded upstream OpenAPI specifications in specs/upstream/ or skill directory.
Verifies schema structure, minimum path counts, OpenAPI version, and key required endpoints.
"""

import sys
from pathlib import Path
import yaml

EXPECTATIONS = {
    "harness-agents-api.yaml": {
        "title": "Harness Agents API",
        "min_paths": 10,
        "required_paths": ["/gitops/api/v1/agents"],
    },
    "harness-applications-api.yaml": {
        "title": "Harness Applications API",
        "min_paths": 15,
        "required_paths": ["/gitops/api/v1/agents/{agentIdentifier}/applications"],
    },
    "harness-catalogcustomproperties-api.yaml": {
        "title": "Harness Catalog Custom Properties API",
        "min_paths": 2,
        "required_paths": ["/v1/catalog/custom-properties"],
    },
    "harness-entities-api.yaml": {
        "title": "Harness Entities API",
        "min_paths": 5,
        "required_paths": ["/v1/entities", "/v1/entities/by-refs"],
    },
    "harness-pipeline-execution-api.yaml": {
        "title": "Harness Pipeline Execution API",
        "min_paths": 5,
        "required_paths": [
            "/v1/orgs/{org}/projects/{project}/pipelines/{pipeline}/execute"
        ],
    },
    "harness-pipelines-api.yaml": {
        "title": "Harness Pipelines API",
        "min_paths": 5,
        "required_paths": [
            "/v1/orgs/{org}/projects/{project}/pipelines",
            "/v1/orgs/{org}/projects/{project}/pipelines/{pipeline}",
        ],
    },
}


def validate_spec(file_path: Path, rules: dict) -> tuple[list[str], dict]:
    errors = []
    if not file_path.exists():
        return [f"File does not exist: {file_path}"], {}

    if file_path.stat().st_size == 0:
        return [f"File is empty: {file_path}"], {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return [f"YAML parsing error in {file_path.name}: {e}"], {}

    if not isinstance(data, dict):
        return [f"Root of {file_path.name} is not a valid YAML object/mapping"], {}

    openapi_version = data.get("openapi")
    if not openapi_version or not str(openapi_version).startswith("3."):
        errors.append(
            f"Invalid or missing OpenAPI version in {file_path.name}: {openapi_version}"
        )

    info = data.get("info", {})
    actual_title = info.get("title", "")
    expected_title = rules.get("title", "")
    if expected_title and expected_title not in actual_title:
        errors.append(
            f"Title mismatch in {file_path.name}: expected '{expected_title}', got '{actual_title}'"
        )

    paths = data.get("paths", {})
    if not isinstance(paths, dict):
        errors.append(f"Missing or invalid 'paths' object in {file_path.name}")
        return errors, data

    min_paths = rules.get("min_paths", 1)
    if len(paths) < min_paths:
        errors.append(
            f"Insufficient paths in {file_path.name}: found {len(paths)}, expected >= {min_paths}"
        )

    for req in rules.get("required_paths", []):
        if req not in paths:
            errors.append(
                f"Missing required path in {file_path.name}: '{req}'"
            )

    return errors, data


def main() -> int:
    search_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("schemas")
    if not search_dir.exists():
        print(f"❌ Error: Directory '{search_dir}' does not exist.")
        return 1

    all_errors = []
    print(f"🔍 Validating specifications in {search_dir}...")

    for filename, rules in EXPECTATIONS.items():
        file_path = search_dir / filename
        if not file_path.exists():
            continue
        file_errors, data = validate_spec(file_path, rules)
        if file_errors:
            all_errors.extend(file_errors)
            print(f"  ❌ {filename} (FAILED)")
            for err in file_errors:
                print(f"     - {err}")
        else:
            openapi_ver = data.get("openapi")
            path_count = len(data.get("paths", {}))
            print(
                f"  ✅ {filename} (OpenAPI {openapi_ver}, {path_count} paths verified)"
            )

    if all_errors:
        print(f"\n❌ Validation failed with {len(all_errors)} error(s).")
        return 1

    print("\n✨ Specifications passed validation successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
