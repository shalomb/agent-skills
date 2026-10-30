# pyright: reportMissingImports=false
"""Unit tests for bounded context and glossary term extraction."""

from pathlib import Path

from understand_glossary.extractor import (
    extract_glossary,
    find_glossary_map,
    infer_contexts_from_areas,
    parse_glossary_map,
)


def test_find_glossary_map_finds_root_glossary_map(tmp_path):
    map_file = tmp_path / "GLOSSARY-MAP.md"
    map_file.write_text("# Glossary Map\n", encoding="utf-8")
    found = find_glossary_map(tmp_path)
    assert found == map_file


def test_find_glossary_map_finds_docs_glossary_map(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    map_file = docs / "GLOSSARY.md"
    map_file.write_text("# Glossary\n", encoding="utf-8")
    found = find_glossary_map(tmp_path)
    assert found == map_file


def test_parse_glossary_map_markdown(tmp_path):
    map_file = tmp_path / "GLOSSARY-MAP.md"
    map_file.write_text(
        "# Glossary Map\n\n"
        "## billing\n"
        "**Invoice**: A bill sent to a customer.\n"
        "**Account**: Payer of invoices.\n\n"
        "## identity\n"
        "**Account**: Login principal.\n"
        "**Session**: Authenticated user session.\n",
        encoding="utf-8",
    )
    contexts = parse_glossary_map(map_file)
    assert len(contexts) == 2
    ctx_names = [c.name for c in contexts]
    assert ctx_names == ["billing", "identity"]

    billing = contexts[0]
    assert len(billing.terms) == 2
    assert billing.terms[0].term == "Invoice"
    assert billing.terms[0].meaning == "A bill sent to a customer."
    assert billing.terms[1].term == "Account"

    identity = contexts[1]
    assert len(identity.terms) == 2
    assert identity.terms[0].term == "Account"
    assert identity.terms[0].meaning == "Login principal."


def test_parse_glossary_map_json(tmp_path):
    map_file = tmp_path / "glossary.json"
    map_file.write_text(
        '{"contexts": [{"name": "runtime", "terms": [{"term": "Config", "meaning": "Server settings."}]}]}',
        encoding="utf-8",
    )
    contexts = parse_glossary_map(map_file)
    assert len(contexts) == 1
    assert contexts[0].name == "runtime"
    assert contexts[0].terms[0].term == "Config"


def test_infer_contexts_from_areas_when_no_map(tmp_path):
    billing_dir = tmp_path / "src" / "billing"
    billing_dir.mkdir(parents=True)
    (billing_dir / "invoice.ts").write_text(
        "// Invoice: bill sent to customer\n"
        "export class Invoice { total: number; }\n"
        "// Account: payer of invoices\n"
        "export class Account { id: string; }\n",
        encoding="utf-8",
    )

    identity_dir = tmp_path / "src" / "identity"
    identity_dir.mkdir(parents=True)
    (identity_dir / "auth.ts").write_text(
        "// Account: login principal\n"
        "export class Account { username: string; }\n"
        "// Token: bearer credentials\n"
        "export class Token { jwt: string; }\n",
        encoding="utf-8",
    )

    contexts = infer_contexts_from_areas(tmp_path)
    ctx_names = {c.name for c in contexts}
    assert {"billing", "identity"} <= ctx_names or {"src/billing", "src/identity"} <= ctx_names

    term_names = {t.term for c in contexts for t in c.terms}
    assert "Account" in term_names
    assert "Invoice" in term_names or "Token" in term_names


def test_extract_glossary_end_to_end_with_collisions_and_draft(tmp_path):
    map_file = tmp_path / "GLOSSARY-MAP.md"
    map_file.write_text(
        "## billing\n"
        "**Account**: payer of invoices\n\n"
        "## identity\n"
        "**Account**: login principal\n",
        encoding="utf-8",
    )
    result = extract_glossary(tmp_path)
    assert len(result.contexts) == 2
    assert len(result.collisions) == 1
    assert result.collisions[0].term == "Account"
    assert "# Glossary" in result.draft
    assert "billing" in result.draft
    assert "identity" in result.draft
