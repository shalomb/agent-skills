# pyright: reportMissingImports=false
"""Mermaid C4 architecture diagram generator for /understand (Spec Unit 3).

Produces valid Mermaid C4Context and C4Container diagrams following the
c4-architecture conventions and Agent Skills specification.
"""

from __future__ import annotations

import re
from typing import Any

# Mermaid C4 macro names and reserved keywords to avoid collision in aliases
_C4_RESERVED = {
    "person", "person_ext", "system", "system_ext", "systemdb", "systemdb_ext",
    "systemqueue", "systemqueue_ext", "container", "container_ext", "containerdb",
    "containerdb_ext", "containerqueue", "containerqueue_ext", "container_boundary",
    "system_boundary", "enterprise_boundary", "boundary", "rel", "birel", "rel_u",
    "rel_d", "rel_l", "rel_r", "rel_back", "relindex", "title", "c4context",
    "c4container", "c4component", "c4dynamic", "c4deployment", "end",
}


def sanitize_alias(name: str, prefix: str = "item") -> str:
    """Produces a safe, alphanumeric Mermaid C4 identifier from an arbitrary string."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())
    clean = re.sub(r"_+", "_", clean).strip("_")
    if not clean or clean[0].isdigit():
        clean = f"{prefix}_{clean}".rstrip("_")
    if clean.lower() in _C4_RESERVED:
        clean = f"{prefix}_{clean}"
    return clean.lower()


def escape_c4_text(text: str) -> str:
    """Escapes and normalizes text for Mermaid C4 macro parameters."""
    if not text:
        return ""
    # Normalize newlines to spaces so we don't break line-based syntax
    cleaned = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    # Replace internal double quotes with single quotes to avoid closing macro string literals
    cleaned = cleaned.replace('"', "'")
    return cleaned.strip()


def generate_c4_context(
    repo_name: str,
    description: str = "",
    external_systems: list[tuple[str, str, str]] | list[Any] | None = None,
) -> str:
    """Generates clean Mermaid C4Context diagram with Person/System/System_Ext blocks and Rel relationships.

    Args:
        repo_name: Name of the repository or primary system.
        description: System intent or description.
        external_systems: List of (name, description, relationship_label) tuples or dicts.

    Returns:
        Mermaid C4Context diagram source code.
    """
    clean_repo = escape_c4_text(repo_name) or "System"
    repo_desc = escape_c4_text(description) or f"Core software system for {clean_repo}"
    sys_alias = sanitize_alias(repo_name or "system", prefix="sys")

    lines: list[str] = [
        "C4Context",
        f"  title System Context diagram for {clean_repo}",
        "",
        f'  Person(user, "User", "Developer or client interacting with {clean_repo}")',
        f'  System({sys_alias}, "{clean_repo}", "{repo_desc}")',
    ]

    ext_lines: list[str] = []
    rel_lines: list[str] = [
        f'  Rel(user, {sys_alias}, "Uses")',
    ]

    used_aliases: set[str] = {"user", sys_alias}

    if external_systems:
        for item in external_systems:
            if isinstance(item, (tuple, list)):
                ext_name = str(item[0]) if len(item) > 0 else "External System"
                ext_desc = str(item[1]) if len(item) > 1 else ""
                ext_rel = str(item[2]) if len(item) > 2 else "Interacts with"
            elif isinstance(item, dict):
                ext_name = str(item.get("name") or item.get("label") or "External System")
                ext_desc = str(item.get("description") or item.get("descr") or "")
                ext_rel = str(item.get("relationship") or item.get("rel") or item.get("relationship_label") or "Interacts with")
            else:
                ext_name = str(item)
                ext_desc = ""
                ext_rel = "Interacts with"

            base_alias = sanitize_alias(ext_name, prefix="ext")
            alias = base_alias
            counter = 2
            while alias in used_aliases:
                alias = f"{base_alias}_{counter}"
                counter += 1
            used_aliases.add(alias)

            esc_name = escape_c4_text(ext_name)
            esc_desc = escape_c4_text(ext_desc)
            esc_rel = escape_c4_text(ext_rel)

            ext_lines.append(f'  System_Ext({alias}, "{esc_name}", "{esc_desc}")')
            rel_lines.append(f'  Rel({sys_alias}, {alias}, "{esc_rel}")')

    if ext_lines:
        lines.append("")
        lines.extend(ext_lines)

    lines.append("")
    lines.extend(rel_lines)
    return "\n".join(lines)


def generate_c4_container(
    repo_name: str,
    containers: list[dict[str, Any]] | None = None,
) -> str:
    """Generates clean Mermaid C4Container diagram with Container_Boundary, Container, and ContainerDb blocks.

    Args:
        repo_name: Name of the repository or system boundary.
        containers: List of container dictionaries. Supported keys:
            - name / label: container display name
            - alias: optional identifier
            - technology / techn: technology or framework stack
            - description / descr: responsibility / role
            - type / kind: "container" | "db" | "database" | "storage" | "cli" | "api" | "core"
            - is_db: bool
            - entry_point: bool
            - relationships / rels / depends_on: list of target aliases or relationship dicts

    Returns:
        Mermaid C4Container diagram source code.
    """
    clean_repo = escape_c4_text(repo_name) or "System"
    bnd_alias = f"bnd_{sanitize_alias(repo_name or 'system', prefix='bnd')}"

    lines: list[str] = [
        "C4Container",
        f"  title Container diagram for {clean_repo}",
        "",
        f'  Person(user, "User", "Developer or client interacting with {clean_repo}")',
        "",
        f'  Container_Boundary({bnd_alias}, "{clean_repo}") {{',
    ]

    if not containers:
        app_alias = sanitize_alias(repo_name or "app", prefix="c")
        lines.append(f'    Container({app_alias}, "{clean_repo}", "Codebase", "Core application modules")')
        lines.append("  }")
        lines.append("")
        lines.append(f'  Rel(user, {app_alias}, "Uses")')
        return "\n".join(lines)

    parsed_containers: list[dict[str, Any]] = []
    used_aliases: set[str] = {"user", bnd_alias}
    alias_lookup: dict[str, str] = {}

    for i, c in enumerate(containers):
        name = str(c.get("name") or c.get("label") or f"Container_{i+1}")
        label = str(c.get("label") or c.get("name") or name)
        alias = c.get("alias")
        if not alias:
            base_alias = sanitize_alias(name, prefix="c")
            alias = base_alias
            counter = 2
            while alias in used_aliases:
                alias = f"{base_alias}_{counter}"
                counter += 1
        used_aliases.add(alias)

        alias_lookup[name.lower()] = alias
        alias_lookup[alias] = alias

        techn = str(c.get("techn") or c.get("technology") or "Software Component")
        descr = str(c.get("descr") or c.get("description") or "")
        kind = str(c.get("type") or c.get("kind") or "").lower()

        name_lower = name.lower()
        is_db = bool(
            c.get("is_db")
            or kind in ("db", "database", "storage", "datastore", "cache", "store", "persistence")
            or any(k in name_lower for k in ("database", "storage", "cache", "postgres", "sqlite", "redis", "mysql", "mongo", "db"))
        )

        is_entry = bool(
            c.get("entry_point")
            or kind in ("cli", "api", "web", "frontend", "gateway", "ui", "runner")
            or any(k in name_lower for k in ("cli", "command", "api", "web", "frontend", "gateway", "ui", "main", "runner"))
        )

        rels = c.get("relationships") or c.get("rels") or c.get("depends_on") or c.get("calls") or c.get("uses") or []

        parsed_containers.append({
            "alias": alias,
            "name": name,
            "label": label,
            "techn": techn,
            "descr": descr,
            "kind": kind,
            "is_db": is_db,
            "is_entry": is_entry,
            "rels": rels,
        })

    # Render container elements inside boundary
    for pc in parsed_containers:
        esc_label = escape_c4_text(pc["label"])
        esc_techn = escape_c4_text(pc["techn"])
        esc_descr = escape_c4_text(pc["descr"])
        if pc["is_db"]:
            lines.append(f'    ContainerDb({pc["alias"]}, "{esc_label}", "{esc_techn}", "{esc_descr}")')
        else:
            lines.append(f'    Container({pc["alias"]}, "{esc_label}", "{esc_techn}", "{esc_descr}")')

    lines.append("  }")
    lines.append("")

    # Build relationships
    rel_lines: list[str] = []
    seen_rels: set[tuple[str, str]] = set()

    def add_rel(src: str, tgt: str, rel_lbl: str, techn_lbl: str = "") -> None:
        if (src, tgt) in seen_rels or src == tgt:
            return
        seen_rels.add((src, tgt))
        esc_lbl = escape_c4_text(rel_lbl)
        if techn_lbl:
            esc_tech = escape_c4_text(techn_lbl)
            rel_lines.append(f'  Rel({src}, {tgt}, "{esc_lbl}", "{esc_tech}")')
        else:
            rel_lines.append(f'  Rel({src}, {tgt}, "{esc_lbl}")')

    # 1. User relationships to entry points
    entry_containers = [pc for pc in parsed_containers if pc["is_entry"]]
    if entry_containers:
        for ec in entry_containers:
            lbl = "Executes" if "cli" in ec["alias"] or "cli" in ec["kind"] else "Uses"
            add_rel("user", ec["alias"], lbl)
    else:
        # Connect to first non-db container or first container
        non_dbs = [pc for pc in parsed_containers if not pc["is_db"]]
        first = non_dbs[0] if non_dbs else parsed_containers[0]
        add_rel("user", first["alias"], "Uses")

    # 2. Check for explicit container-to-container relationships
    has_explicit_rels = False
    for pc in parsed_containers:
        src_alias = pc["alias"]
        for r in pc["rels"]:
            if isinstance(r, dict):
                raw_tgt = str(r.get("target") or r.get("to") or "")
                lbl = str(r.get("label") or "Uses")
                techn = str(r.get("techn") or r.get("technology") or "")
            elif isinstance(r, (tuple, list)):
                raw_tgt = str(r[0]) if len(r) > 0 else ""
                lbl = str(r[1]) if len(r) > 1 else "Uses"
                techn = str(r[2]) if len(r) > 2 else ""
            else:
                raw_tgt = str(r)
                lbl = "Uses"
                techn = ""

            resolved_tgt = alias_lookup.get(raw_tgt.lower(), raw_tgt)
            if resolved_tgt in used_aliases:
                add_rel(src_alias, resolved_tgt, lbl, techn)
                has_explicit_rels = True

    # 3. If no explicit relationships were provided, infer logical flow between architectural tiers
    if not has_explicit_rels:
        entries = [pc for pc in parsed_containers if pc["is_entry"]]
        databases = [pc for pc in parsed_containers if pc["is_db"]]
        logic_tier = [pc for pc in parsed_containers if not pc["is_entry"] and not pc["is_db"]]

        if entries and logic_tier:
            for e in entries:
                for l_pc in logic_tier:
                    add_rel(e["alias"], l_pc["alias"], "Invokes")
        elif entries and databases:
            for e in entries:
                for d in databases:
                    add_rel(e["alias"], d["alias"], "Reads/writes")

        if logic_tier and databases:
            for l_pc in logic_tier:
                for d in databases:
                    add_rel(l_pc["alias"], d["alias"], "Reads/writes")
        elif not entries and not databases and len(parsed_containers) > 1:
            for i in range(len(parsed_containers) - 1):
                add_rel(parsed_containers[i]["alias"], parsed_containers[i+1]["alias"], "Calls")

    lines.extend(rel_lines)
    return "\n".join(lines)
