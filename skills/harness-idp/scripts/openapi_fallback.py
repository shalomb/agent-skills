#!/usr/bin/env python3
"""
OpenAPI Fallback Resolver for Harness IDP Skill

Use when an API endpoint is not explicitly documented in the skill.
Automatically downloads and queries the official spec.

Usage in code:
    from openapi_fallback import resolve_endpoint
    
    docs = resolve_endpoint("/pipeline/api/pipelines/execute", method="POST")
    if docs:
        print(docs)
    else:
        print("Could not resolve endpoint")
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import urllib.request
import urllib.error

# Use shared discovery module
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))

try:
    from openapi_discovery import load_spec, get_endpoint_docs, search_endpoints, find_related
except ImportError:
    # Fallback if running outside skill directory
    print("Warning: Could not import openapi_discovery module", file=sys.stderr)
    load_spec = None


class OpenAPIResolver:
    """Resolve Harness API documentation from OpenAPI spec"""
    
    def __init__(self, refresh: bool = False):
        self.spec = load_spec(refresh=refresh) if load_spec else None
        self.available = self.spec is not None
    
    def resolve_endpoint(self, path: str, method: Optional[str] = None) -> Optional[str]:
        """Get documentation for an endpoint"""
        if not self.available:
            return None
        return get_endpoint_docs(self.spec, path, method)
    
    def search(self, query: str) -> list:
        """Search for endpoints matching query"""
        if not self.available:
            return []
        return search_endpoints(self.spec, query)
    
    def suggest(self, keyword: str) -> Optional[str]:
        """Suggest related endpoints"""
        if not self.available:
            return None
        return find_related(self.spec, keyword, limit=5)
    
    def get_endpoint_summary(self, path: str) -> Optional[str]:
        """Get just the summary line for an endpoint"""
        if not self.available:
            return None
        
        # Quick lookup
        for p, methods in self.spec.get("paths", {}).items():
            if p == path or p.rstrip("/") == path.rstrip("/"):
                for method, details in methods.items():
                    if method in ('get', 'post', 'put', 'delete', 'patch'):
                        return details.get("summary", "")
        return None


def resolve_endpoint(path: str, method: Optional[str] = None, refresh: bool = False) -> Optional[str]:
    """Convenience function: resolve endpoint documentation"""
    resolver = OpenAPIResolver(refresh=refresh)
    return resolver.resolve_endpoint(path, method)


def search_endpoints_by_keyword(query: str) -> list:
    """Convenience function: search endpoints"""
    resolver = OpenAPIResolver()
    return resolver.search(query)


def suggest_related(keyword: str) -> Optional[str]:
    """Convenience function: get suggestions"""
    resolver = OpenAPIResolver()
    return resolver.suggest(keyword)


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: openapi_fallback.py <endpoint> [method]")
        print("Example: openapi_fallback.py /pipeline/api/pipelines/execute POST")
        sys.exit(1)
    
    endpoint = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else None
    
    docs = resolve_endpoint(endpoint, method)
    if docs:
        print(docs)
    else:
        print(f"Could not find documentation for {endpoint}", file=sys.stderr)
        sys.exit(1)
