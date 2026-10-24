#!/usr/bin/env python3
"""
Executes or triggers a Harness Pipeline via REST API.
Follows 12-factor configuration (CLI args -> ENV -> ~/.config/harness/<profile>).

Usage:
    python3 execute_pipeline.py --pipeline <pipeline-id> [--org <org-id>] [--project <project-id>] [--inputs <inputs.yaml>]
"""

import sys
import json
import argparse
from pathlib import Path
import requests
import yaml

from harness_config import load_harness_config


def trigger_pipeline(
    pipeline_id: str,
    org_id: str,
    project_id: str,
    inputs: dict = None,
    cfg=None,
) -> dict:
    if cfg is None:
        cfg = load_harness_config(org_id=org_id, project_id=project_id)

    org = org_id or cfg.org_id
    project = project_id or cfg.project_id

    if not org or not project:
        raise ValueError("Both org_id and project_id are required to execute a pipeline.")

    # Endpoint from specs/upstream/harness-pipeline-execution-api.yaml
    endpoint = (
        f"{cfg.base_url}/gateway/pipeline/api/pipeline/execute/{pipeline_id}"
        f"?accountIdentifier={cfg.account_id}&orgIdentifier={org}&projectIdentifier={project}"
    )

    payload = inputs or {}
    resp = requests.post(endpoint, json=payload, headers=cfg.headers(), timeout=30)
    if not resp.ok:
        raise RuntimeError(
            f"Failed to execute pipeline ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Trigger Harness Pipeline Execution")
    parser.add_argument("--pipeline", required=True, help="Pipeline Identifier")
    parser.add_argument("--org", help="Harness Org Identifier (defaults to config)")
    parser.add_argument("--project", help="Harness Project Identifier (defaults to config)")
    parser.add_argument("--inputs", help="Path to runtime input YAML / JSON file")

    args = parser.parse_args()

    inputs_dict = {}
    if args.inputs:
        with open(args.inputs, "r", encoding="utf-8") as f:
            inputs_dict = yaml.safe_load(f) or {}

    try:
        cfg = load_harness_config(org_id=args.org, project_id=args.project)
        print(f"🚀 Triggering pipeline '{args.pipeline}' using profile from {cfg.source}...")
        result = trigger_pipeline(
            pipeline_id=args.pipeline,
            org_id=args.org,
            project_id=args.project,
            inputs=inputs_dict,
            cfg=cfg,
        )
        print("✅ Pipeline execution initiated:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
