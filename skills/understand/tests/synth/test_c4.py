# pyright: reportMissingImports=false
"""Unit tests for Mermaid C4 architecture diagram generator (Spec Unit 3 & c4-architecture)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from understand_synth.c4 import (  # noqa: E402
    escape_c4_text,
    generate_c4_container,
    generate_c4_context,
    sanitize_alias,
)


class TestC4Helpers:
    """Tests for sanitization and escaping utilities."""

    def test_sanitize_alias_simple(self):
        assert sanitize_alias("my-repo") == "my_repo"
        assert sanitize_alias("Core_Engine") == "core_engine"
        assert sanitize_alias("service.api") == "service_api"

    def test_sanitize_alias_starting_with_digit(self):
        assert sanitize_alias("123service", prefix="sys") == "sys_123service"

    def test_sanitize_alias_reserved_words(self):
        assert sanitize_alias("system", prefix="sys") == "sys_system"
        assert sanitize_alias("person", prefix="user") == "user_person"
        assert sanitize_alias("rel", prefix="elem") == "elem_rel"

    def test_escape_c4_text(self):
        text = 'This is a "quoted" string\nwith multiple\r\nlines.'
        escaped = escape_c4_text(text)
        assert '"' not in escaped
        assert "'" in escaped
        assert "\n" not in escaped
        assert "\r" not in escaped
        assert "This is a 'quoted' string with multiple lines." == escaped


class TestC4Context:
    """Tests for C4Context diagram generation."""

    def test_generate_c4_context_basic(self):
        diagram = generate_c4_context("my-app", "An application for managing data")
        assert diagram.startswith("C4Context")
        assert "title System Context diagram for my-app" in diagram
        assert 'Person(user, "User"' in diagram
        assert 'System(my_app, "my-app", "An application for managing data")' in diagram
        assert 'Rel(user, my_app, "Uses")' in diagram

    def test_generate_c4_context_with_external_systems(self):
        external_systems = [
            ("GitHub", "Remote Git repository and pull requests", "Reads PR metadata"),
            ("Auth0", "Identity and access management", "Authenticates users via HTTPS"),
            ("PostgreSQL", "Core relational data store", "Reads and writes data"),
        ]
        diagram = generate_c4_context("payment-svc", "Payment processing service", external_systems)

        assert "C4Context" in diagram
        assert 'title System Context diagram for payment-svc' in diagram
        assert 'System(payment_svc, "payment-svc", "Payment processing service")' in diagram

        # External systems
        assert 'System_Ext(github, "GitHub", "Remote Git repository and pull requests")' in diagram
        assert 'System_Ext(auth0, "Auth0", "Identity and access management")' in diagram
        assert 'System_Ext(postgresql, "PostgreSQL", "Core relational data store")' in diagram

        # Relationships
        assert 'Rel(user, payment_svc, "Uses")' in diagram
        assert 'Rel(payment_svc, github, "Reads PR metadata")' in diagram
        assert 'Rel(payment_svc, auth0, "Authenticates users via HTTPS")' in diagram
        assert 'Rel(payment_svc, postgresql, "Reads and writes data")' in diagram

    def test_generate_c4_context_escaping(self):
        desc = 'Handles "critical" orders\nand transactions'
        ext = [('Stripe "v3" API', 'External "payment" gateway\nover TLS', 'Sends "charges"')]
        diagram = generate_c4_context('my "store" app', desc, ext)

        assert '"critical"' not in diagram
        assert "'critical'" in diagram
        assert "\nand" not in diagram
        assert 'System_Ext(' in diagram
        assert 'Rel(' in diagram

    def test_generate_c4_context_empty_defaults(self):
        diagram = generate_c4_context("", "")
        assert "C4Context" in diagram
        assert "Person(user" in diagram
        assert "System(" in diagram
        assert "Rel(user" in diagram


class TestC4Container:
    """Tests for C4Container diagram generation."""

    def test_generate_c4_container_basic(self):
        containers = [
            {
                "name": "CLI Tool",
                "type": "cli",
                "technology": "Python / Click",
                "description": "Command line interface for users",
                "entry_point": True,
            },
            {
                "name": "Core Engine",
                "type": "core",
                "technology": "Python",
                "description": "Business logic and report synthesis",
            },
            {
                "name": "Shadow Storage",
                "type": "database",
                "technology": "File System / JSON",
                "description": "Stores generated report bundles and run caches",
                "is_db": True,
            },
        ]
        diagram = generate_c4_container("understand", containers)

        assert diagram.startswith("C4Container")
        assert "title Container diagram for understand" in diagram
        assert 'Person(user, "User"' in diagram
        assert 'Container_Boundary(bnd_understand, "understand") {' in diagram

        # Verify Container and ContainerDb blocks
        assert 'Container(cli_tool, "CLI Tool", "Python / Click", "Command line interface for users")' in diagram
        assert 'Container(core_engine, "Core Engine", "Python", "Business logic and report synthesis")' in diagram
        assert 'ContainerDb(shadow_storage, "Shadow Storage", "File System / JSON", "Stores generated report bundles and run caches")' in diagram

        # Verify boundary closing
        assert "  }" in diagram

        # Verify inferred relationships
        assert 'Rel(user, cli_tool, "Executes")' in diagram or 'Rel(user, cli_tool, "Uses")' in diagram
        assert 'Rel(cli_tool, core_engine, "Invokes")' in diagram or 'Rel(cli_tool, core_engine, "Uses")' in diagram
        assert 'Rel(core_engine, shadow_storage, "Reads/writes")' in diagram or 'Rel(core_engine, shadow_storage, "Uses")' in diagram

    def test_generate_c4_container_db_detection(self):
        containers = [
            {"name": "API Service", "type": "api", "technology": "FastAPI", "description": "REST endpoints"},
            {"name": "Postgres Database", "type": "db", "technology": "PostgreSQL", "description": "Persistent data"},
            {"name": "Redis Cache", "type": "cache", "technology": "Redis", "description": "Session caching"},
        ]
        diagram = generate_c4_container("web-platform", containers)

        assert 'Container(api_service, "API Service", "FastAPI", "REST endpoints")' in diagram
        assert 'ContainerDb(postgres_database, "Postgres Database", "PostgreSQL", "Persistent data")' in diagram
        assert 'ContainerDb(redis_cache, "Redis Cache", "Redis", "Session caching")' in diagram

    def test_generate_c4_container_explicit_relationships(self):
        containers = [
            {
                "name": "Web UI",
                "alias": "ui",
                "type": "web",
                "technology": "React / TypeScript",
                "description": "Frontend single page application",
                "relationships": [
                    {"target": "api", "label": "Sends requests", "technology": "JSON/HTTPS"},
                ],
            },
            {
                "name": "API Gateway",
                "alias": "api",
                "type": "api",
                "technology": "Node.js",
                "description": "Backend API gateway",
                "relationships": [
                    {"target": "db", "label": "Queries and saves", "technology": "SQL"},
                ],
            },
            {
                "name": "Database",
                "alias": "db",
                "type": "database",
                "technology": "PostgreSQL",
                "description": "User records",
                "is_db": True,
            },
        ]
        diagram = generate_c4_container("portal", containers)

        assert 'Rel(ui, api, "Sends requests", "JSON/HTTPS")' in diagram
        assert 'Rel(api, db, "Queries and saves", "SQL")' in diagram

    def test_generate_c4_container_empty_containers(self):
        diagram = generate_c4_container("empty-repo", [])
        assert "C4Container" in diagram
        assert "Container_Boundary(" in diagram
        assert "Container(" in diagram
        assert "Rel(user," in diagram

    def test_c4_syntax_conformance(self):
        """Ensures all generated lines conform to valid Mermaid C4 macro syntax."""
        diagram = generate_c4_container(
            "complex-system",
            [
                {"name": "CLI", "type": "cli", "technology": "Bash", "description": "Script"},
                {"name": "Engine", "type": "core", "technology": "Python", "description": "Core"},
                {"name": "Store", "type": "storage", "technology": "SQLite", "description": "Storage"},
            ],
        )

        # Boundary braces balance
        assert diagram.count("{") == diagram.count("}")

        # Check macro patterns
        macro_pattern = re.compile(
            r"^\s*(?:Person|Person_Ext|System|System_Ext|Container|ContainerDb|Rel)\([a-zA-Z0-9_]+,\s*\"[^\"]*\".*\)$"
        )
        non_macro_keywords = (
            "C4Context", "C4Container", "title ", "Container_Boundary", "}", ""
        )

        for line in diagram.splitlines():
            trimmed = line.strip()
            if not trimmed or any(trimmed.startswith(kw) for kw in non_macro_keywords):
                continue
            assert macro_pattern.match(trimmed), f"Invalid Mermaid C4 macro call: {trimmed}"
