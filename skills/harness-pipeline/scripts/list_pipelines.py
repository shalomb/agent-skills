#!/usr/bin/env python3
"""
Lists all Harness Pipelines across projects within an organization.
Follows 12-factor configuration (CLI args -> ENV -> ~/.config/harness/<profile>).

Usage:
    python3 list_pipelines.py [--org <org-id>] [--project <project-id>]
"""

import sys
import argparse
import requests

from harness_config import load_harness_config


def get_projects(cfg, org: str) -> list[dict]:
    url = f"{cfg.base_url}/v1/orgs/{org}/projects?limit=100"
    headers = {**cfg.headers(), "Harness-Account": cfg.account_id}
    resp = requests.get(url, headers=headers, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Failed to fetch projects ({resp.status_code}): {resp.text}")
    data = resp.json()
    if isinstance(data, list):
        return [p.get("project", p) for p in data]
    return []


def get_pipelines(cfg, org: str, project_id: str) -> list[dict]:
    url = f"{cfg.base_url}/v1/orgs/{org}/projects/{project_id}/pipelines?limit=100"
    headers = {**cfg.headers(), "Harness-Account": cfg.account_id}
    resp = requests.get(url, headers=headers, timeout=30)
    if not resp.ok:
        return []
    return resp.json() if isinstance(resp.json(), list) else []


def main():
    parser = argparse.ArgumentParser(description="List Harness Pipelines across Org / Projects")
    parser.add_argument("--org", help="Harness Organization Identifier")
    parser.add_argument("--project", help="Optional specific Project Identifier")

    args = parser.parse_args()

    try:
        cfg = load_harness_config(org_id=args.org, project_id=args.project)
        target_org = args.org or cfg.org_id
        if not target_org:
            raise ValueError("Organization identifier is required (pass --org or set in profile).")

        print(f"🔍 Querying Harness Org '{target_org}' using credentials from {cfg.source}...\n")

        if args.project:
            projects = [{"identifier": args.project, "name": args.project}]
        else:
            projects = get_projects(cfg, target_org)

        total_pipelines = 0
        for p in projects:
            p_id = p.get("identifier")
            p_name = p.get("name", p_id)
            pipelines = get_pipelines(cfg, target_org, p_id)
            print(f"📁 Project: {p_name} (`{p_id}`)")
            print(f"   Pipelines ({len(pipelines)}):")
            for pipe in pipelines:
                total_pipelines += 1
                pid = pipe.get("identifier")
                pname = pipe.get("name")
                store = pipe.get("store_type", "INLINE")
                git_details = pipe.get("git_details") or {}
                if store == "REMOTE" and git_details:
                    store_info = f"[REMOTE -> {git_details.get('repo_name')}:{git_details.get('file_path')}]"
                else:
                    store_info = "[INLINE]"
                print(f"   • {pid:36} | {pname:42} | {store_info}")
            print()

        print(f"✨ Found {total_pipelines} total pipelines across {len(projects)} project(s) in org '{target_org}'.")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
