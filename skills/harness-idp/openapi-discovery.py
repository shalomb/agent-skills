#!/usr/bin/env python3
"""
OpenAPI Spec Discovery & Query Tool for Harness APIs

Automatically downloads and queries the official Harness OpenAPI spec
to provide fallback documentation for undocumented endpoints.

Usage:
  python3 openapi-discovery.py --search "pipeline execution"
  python3 openapi-discovery.py --endpoint "/pipeline/api/pipelines/execute"
  python3 openapi-discovery.py --list-modules
  python3 openapi-discovery.py --refresh
"""

import json
import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import urllib.request
import urllib.error

# Configuration
SPEC_DOWNLOAD_URL = "https://apidocs.harness.io/_bundle/index.json?download"
SPEC_YAML_URL = "https://apidocs.harness.io/_bundle/index.yaml?download"
CACHE_DIR = Path(__file__).parent / "openapi-cache"
CACHE_FILE = CACHE_DIR / "harness-openapi.json"
MANIFEST_FILE = CACHE_DIR / "manifest.json"

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True)


def download_spec(url: str, output_path: Path) -> bool:
    """Download OpenAPI spec from apidocs.harness.io"""
    try:
        print(f"Downloading Harness OpenAPI spec from {url}...", file=sys.stderr)
        with urllib.request.urlopen(url, timeout=30) as response:
            spec = response.read()
            output_path.write_bytes(spec)
        size_mb = len(spec) / (1024 * 1024)
        print(f"✓ Downloaded {size_mb:.1f}MB to {output_path}", file=sys.stderr)
        return True
    except urllib.error.URLError as e:
        print(f"✗ Failed to download spec: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return False


def load_spec(refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Load cached spec, or download if missing/expired"""
    
    # Check if cache exists and is recent (< 7 days)
    if CACHE_FILE.exists() and not refresh:
        age_days = (datetime.now() - datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)).days
        if age_days < 7:
            print(f"Using cached spec ({age_days}d old)", file=sys.stderr)
            try:
                return json.loads(CACHE_FILE.read_text())
            except json.JSONDecodeError:
                print("Cache corrupted, re-downloading...", file=sys.stderr)
    
    # Download fresh spec
    if not download_spec(SPEC_DOWNLOAD_URL, CACHE_FILE):
        if CACHE_FILE.exists():
            print("Using stale cache as fallback", file=sys.stderr)
            return json.loads(CACHE_FILE.read_text())
        return None
    
    # Load and validate
    try:
        spec = json.loads(CACHE_FILE.read_text())
        # Save manifest with metadata
        manifest = {
            "downloaded_at": datetime.now().isoformat(),
            "spec_version": spec.get("info", {}).get("version"),
            "total_endpoints": len(spec.get("paths", {})),
            "modules": list(set(p.strip("/").split("/")[0] for p in spec.get("paths", {})))
        }
        MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))
        return spec
    except Exception as e:
        print(f"Failed to load spec: {e}", file=sys.stderr)
        return None


def search_endpoints(spec: Dict, query: str) -> List[tuple]:
    """Search endpoints by keyword"""
    query_lower = query.lower()
    matches = []
    
    for path, methods in spec.get("paths", {}).items():
        path_match = query_lower in path.lower()
        for method, details in methods.items():
            if method not in ('get', 'post', 'put', 'delete', 'patch'):
                continue
            
            summary = (details.get("summary") or "").lower()
            desc = (details.get("description") or "").lower()
            summary_match = query_lower in summary or query_lower in desc
            
            if path_match or summary_match:
                matches.append((path, method.upper(), details.get("summary", "")))
    
    return sorted(set(matches))


def get_endpoint_docs(spec: Dict, path: str, method: str = None) -> str:
    """Get detailed documentation for an endpoint"""
    
    # Try exact match first
    if path not in spec.get("paths", {}):
        # Try normalized version
        normalized = re.sub(r'\{[^}]+\}', '{ID}', path)
        for p in spec.get("paths", {}):
            if re.sub(r'\{[^}]+\}', '{ID}', p) == normalized:
                path = p
                break
        else:
            return f"Endpoint not found: {path}"
    
    entry = spec["paths"][path]
    methods_available = [m for m in ('get', 'post', 'put', 'delete', 'patch') if m in entry]
    
    if not methods_available:
        return f"No operations found for {path}"
    
    # Default to first available or specified method
    if method:
        method = method.lower()
        if method not in methods_available:
            return f"Method {method.upper()} not available. Available: {', '.join(m.upper() for m in methods_available)}"
    else:
        method = methods_available[0]
    
    op = entry[method]
    docs = []
    docs.append(f"\n{'='*80}")
    docs.append(f"  {method.upper():6} {path}")
    docs.append('='*80)
    
    # Summary & description
    summary = op.get("summary", "")
    if summary:
        docs.append(f"\nSummary: {summary}")
    
    description = op.get("description", "")
    if description:
        docs.append(f"\nDescription: {description[:500]}")
    
    # Parameters
    params = op.get("parameters", [])
    if params:
        docs.append("\n▸ PARAMETERS:")
        for p in params:
            required = "* " if p.get("required") else "  "
            param_in = p.get("in", "")
            param_type = p.get("schema", {}).get("type") if "schema" in p else "string"
            param_desc = (p.get("description") or "")[:70]
            docs.append(f"  {required}{p['name']:<35} ({param_in:6} {param_type:8}) {param_desc}")
    
    # Request body
    body = op.get("requestBody", {})
    if body:
        required = " [required]" if body.get("required") else " [optional]"
        docs.append(f"\n▸ REQUEST BODY{required}:")
        content = body.get("content", {})
        for ct in content:
            docs.append(f"  Content-Type: {ct}")
            schema = content[ct].get("schema", {})
            if "$ref" in schema:
                ref_name = schema["$ref"].split("/")[-1]
                docs.append(f"    Schema: {ref_name}")
            elif schema.get("type") == "object":
                for k in list(schema.get("properties", {}).keys())[:5]:
                    v = schema["properties"][k]
                    vtype = v.get("type") or v.get("$ref", "").split("/")[-1]
                    docs.append(f"      {k}: {vtype}")
                if len(schema.get("properties", {})) > 5:
                    docs.append(f"      ... + {len(schema['properties'])-5} more")
    
    # Responses
    responses = op.get("responses", {})
    if responses:
        docs.append(f"\n▸ RESPONSES:")
        for code, resp in sorted(responses.items()):
            rdesc = (resp.get("description") or "")[:60]
            content = resp.get("content", {})
            rtype = ""
            for _, ct_val in content.items():
                schema = ct_val.get("schema", {})
                rtype = schema.get("$ref", "").split("/")[-1] or schema.get("type", "")
                break
            docs.append(f"  {code}: {rdesc} [{rtype}]")
    
    docs.append(f"\n{'='*80}\n")
    return "\n".join(docs)


def list_modules(spec: Dict) -> str:
    """List all API modules"""
    from collections import defaultdict
    modules = defaultdict(int)
    
    for path in spec.get("paths", {}):
        module = path.strip("/").split("/")[0]
        modules[module] += 1
    
    lines = ["Harness API Modules:\n"]
    for module, count in sorted(modules.items(), key=lambda x: -x[1]):
        lines.append(f"  {module:<15} {count:>4} endpoints")
    
    return "\n".join(lines)


def find_related(spec: Dict, keyword: str, limit: int = 10) -> str:
    """Find related endpoints by keyword"""
    matches = search_endpoints(spec, keyword)
    
    if not matches:
        return f"No endpoints found matching '{keyword}'"
    
    lines = [f"\nEndpoints matching '{keyword}' ({len(matches)} total, showing first {limit}):"]
    lines.append("")
    
    for path, method, summary in matches[:limit]:
        lines.append(f"  [{method:<6}] {path}")
        if summary:
            lines.append(f"           → {summary[:70]}")
    
    if len(matches) > limit:
        lines.append(f"\n  ... and {len(matches) - limit} more. Use --search for full results.")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Harness OpenAPI Spec Discovery & Query",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  openapi-discovery.py --search "pipeline execution"
  openapi-discovery.py --endpoint "/pipeline/api/pipelines/execute"
  openapi-discovery.py --endpoint "/pipeline/api/pipelines/execute" --method POST
  openapi-discovery.py --list-modules
  openapi-discovery.py --refresh
  openapi-discovery.py --find-related "webhook"
        """
    )
    
    parser.add_argument("--search", help="Search endpoints by keyword")
    parser.add_argument("--endpoint", help="Get detailed docs for an endpoint path")
    parser.add_argument("--method", help="Specify HTTP method (GET, POST, etc.)")
    parser.add_argument("--list-modules", action="store_true", help="List all API modules")
    parser.add_argument("--find-related", help="Find related endpoints")
    parser.add_argument("--refresh", action="store_true", help="Force re-download spec")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    # Load spec
    spec = load_spec(refresh=args.refresh)
    if not spec:
        print("ERROR: Could not load OpenAPI spec", file=sys.stderr)
        sys.exit(1)
    
    # Process commands
    if args.search:
        matches = search_endpoints(spec, args.search)
        if args.output == "json":
            print(json.dumps([{"path": p, "method": m, "summary": s} for p, m, s in matches]))
        else:
            print(f"\nFound {len(matches)} endpoints matching '{args.search}':\n")
            for path, method, summary in matches:
                print(f"  [{method:<6}] {path}")
                if summary:
                    print(f"           → {summary}")
    
    elif args.endpoint:
        docs = get_endpoint_docs(spec, args.endpoint, args.method)
        if args.output == "json":
            print(json.dumps({"endpoint": args.endpoint, "documentation": docs}))
        else:
            print(docs)
    
    elif args.list_modules:
        print(list_modules(spec))
    
    elif args.find_related:
        print(find_related(spec, args.find_related))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
