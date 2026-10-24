#!/usr/bin/env python3
"""
Retrieves and exports a Harness Pipeline YAML document via REST API.
Supports both INLINE and REMOTE (Git-synced) pipelines.
Follows 12-factor configuration (CLI args -> ENV -> ~/.config/harness/<profile>).

Usage:
    python3 get_pipeline.py --pipeline <pipeline-id> [--org <org-id>] [--project <project-id>] \
        [--connector-ref <ref>] [--repo-name <repo>] [--branch <branch>] [--output <file.yaml>]
"""

import sys
import argparse
from pathlib import Path
import requests

from harness_config import load_harness_config


def fetch_pipeline(
    pipeline_id: str,
    org_id: str = None,
    project_id: str = None,
    connector_ref: str = None,
    repo_name: str = None,
    branch: str = None,
    cfg = None,
) -> dict:
    if cfg is None:
        cfg = load_harness_config(org_id=org_id, project_id=project_id)

    org = org_id or cfg.org_id
    project = project_id or cfg.project_id

    if not org or not project:
        raise ValueError("Both org_id and project_id are required to fetch a pipeline.")

    endpoint = f"{cfg.base_url}/v1/orgs/{org}/projects/{project}/pipelines/{pipeline_id}"
    headers = {
        **cfg.headers(),
        "Harness-Account": cfg.account_id,
    }

    params = {}
    if connector_ref:
        params["connector_ref"] = connector_ref
    if repo_name:
        params["repo_name"] = repo_name
    if branch:
        params["branch"] = branch
        params["load_from_fallback_branch"] = True

    resp = requests.get(endpoint, headers=headers, params=params, timeout=30)
    if not resp.ok:
        raise RuntimeError(
            f"Failed to fetch pipeline '{pipeline_id}' ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Fetch and export Harness Pipeline YAML")
    parser.add_argument("--pipeline", required=True, help="Pipeline Identifier")
    parser.add_argument("--org", help="Harness Org Identifier")
    parser.add_argument("--project", help="Harness Project Identifier")
    parser.add_argument("--connector-ref", help="Git Connector Reference (for REMOTE Git-synced pipelines)")
    parser.add_argument("--repo-name", help="Repository Name (for REMOTE Git-synced pipelines)")
    parser.add_argument("--branch", help="Git Branch (for REMOTE Git-synced pipelines)")
    parser.add_argument("--output", help="Output file path (prints to stdout if omitted)")

    args = parser.parse_args()

    try:
        cfg = load_harness_config(org_id=args.org, project_id=args.project)
        data = fetch_pipeline(
            args.pipeline,
            org_id=args.org,
            project_id=args.project,
            connector_ref=args.connector_ref,
            repo_name=args.repo_name,
            branch=args.branch,
            cfg=cfg,
        )
        pipe_yaml = data.get("pipeline_yaml", "")

        git_details = data.get("git_details")
        if git_details:
            print(f"ℹ️ Git-synced pipeline: repo={git_details.get('repo_name')}, branch={git_details.get('branch_name')}, file={git_details.get('file_path')}", file=sys.stderr)

        if not pipe_yaml:
            print("⚠️ Warning: Response did not contain 'pipeline_yaml'", file=sys.stderr)

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(pipe_yaml)
            print(f"✅ Pipeline '{args.pipeline}' exported to {out_path} ({len(pipe_yaml)} bytes)")
        else:
            print(pipe_yaml)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
