#!/usr/bin/env python3
"""
Inspects and exports a Harness IDP Scaffolder Template.
Follows 12-factor configuration (CLI args -> ENV -> ~/.config/harness/<profile>).

Usage:
    python3 get_template.py --template <template-name> [--namespace <account|default>] [--json]
"""

import sys
import json
import argparse
import requests
import yaml

from harness_config import load_harness_config


def fetch_template(template_name: str, namespace: str = "account", cfg = None) -> dict:
    if cfg is None:
        cfg = load_harness_config()

    idp_url = f"https://idp.harness.io/{cfg.account_id}/idp/api/catalog/entities/by-name/template/{namespace}/{template_name}"
    headers = {"x-api-key": cfg.api_key}

    resp = requests.get(idp_url, headers=headers, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Failed to fetch template '{template_name}' ({resp.status_code}): {resp.text}")
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Inspect Harness IDP Scaffolder Template")
    parser.add_argument("--template", required=True, help="Template Name")
    parser.add_argument("--namespace", default="account", help="Template Namespace (default: account)")
    parser.add_argument("--json", action="store_true", help="Output full raw JSON")

    args = parser.parse_args()

    try:
        cfg = load_harness_config()
        data = fetch_template(args.template, namespace=args.namespace, cfg=cfg)

        if args.json:
            print(json.dumps(data, indent=2))
            return

        meta = data.get("metadata", {})
        spec = data.get("spec", {})

        print(f"📋 Template: {meta.get('title', args.template)} (`{meta.get('name')}`)")
        print(f"   Namespace:   {meta.get('namespace')}")
        print(f"   Description: {meta.get('description')}")
        print(f"   Owner:       {spec.get('owner')}")
        print(f"   Tags:        {', '.join(meta.get('tags', []))}\n")

        print("📝 Input Parameters (Form Steps):")
        for idx, param_step in enumerate(spec.get("parameters", [])):
            title = param_step.get("title", f"Step {idx+1}")
            req = param_step.get("required", [])
            print(f"  [{idx+1}] {title}")
            for field, field_info in param_step.get("properties", {}).items():
                req_badge = "(required)" if field in req else "(optional)"
                enum_vals = f" -> enum: {field_info.get('enum')}" if "enum" in field_info else ""
                print(f"      • {field} {req_badge}: {field_info.get('title', '')} [{field_info.get('type')}]{enum_vals}")

        print("\n⚡ Execution Workflow Steps:")
        for idx, step in enumerate(spec.get("steps", [])):
            print(f"  [{idx+1}] {step.get('name')} (action: `{step.get('action')}`)")
            input_data = step.get("input", {})
            for k, v in input_data.items():
                print(f"      - {k}: {v}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
