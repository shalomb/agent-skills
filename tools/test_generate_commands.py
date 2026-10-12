#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Unit tests for tools/generate_commands.py."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.generate_commands import (
    ALIAS_MARKER,
    format_instructions_list,
    generate_artifacts,
    install_antigravity_aliases,
    render_antigravity_alias,
    render_claude_command,
    render_pi_extension,
    render_pi_prompt,
    validate_registry,
)


class TestGenerateCommands(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name)
        self.skills_dir = self.repo_dir / "skills"
        self.skills_dir.mkdir(parents=True)

        # Create a mock backing skill
        mock_skill = self.skills_dir / "test-skill"
        mock_skill.mkdir()
        (mock_skill / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: A test skill\n---\n# Test Skill\n",
            encoding="utf-8",
        )

        self.valid_cmd = {
            "name": "test",
            "skill": "test-skill",
            "title": "Test Command",
            "description": "Run test workflows",
            "default_action": "running test workflows",
            "instructions": [
                "Step one of instructions.",
                "Step two with sub-points:\n   - sub 1\n   - sub 2",
            ],
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_format_instructions_list(self) -> None:
        raw = ["Step one.", "Step two with details:\n   - detail A\n   - detail B"]
        formatted = format_instructions_list(raw, start_index=1)
        expected = (
            "1. Step one.\n2. Step two with details:\n   - detail A\n   - detail B"
        )
        self.assertEqual(formatted, expected)

    def test_validate_registry_success(self) -> None:
        data = {"commands": [self.valid_cmd]}
        errors = validate_registry(data, self.repo_dir)
        self.assertEqual(errors, [])

    def test_validate_registry_missing_fields(self) -> None:
        data = {"commands": [{"name": "incomplete"}]}
        errors = validate_registry(data, self.repo_dir)
        self.assertTrue(any("missing 'skill'" in e for e in errors))
        self.assertTrue(any("missing 'description'" in e for e in errors))

    def test_validate_registry_invalid_name(self) -> None:
        data = {
            "commands": [
                {
                    "name": "Bad Name!",
                    "skill": "test-skill",
                    "description": "desc",
                }
            ]
        }
        errors = validate_registry(data, self.repo_dir)
        self.assertTrue(any("invalid name" in e for e in errors))

    def test_validate_registry_missing_backing_skill(self) -> None:
        data = {
            "commands": [
                {
                    "name": "ghost",
                    "skill": "non-existent-skill",
                    "description": "Ghost command",
                }
            ]
        }
        errors = validate_registry(data, self.repo_dir)
        self.assertTrue(any("does not exist" in e for e in errors))

    def test_validate_registry_duplicates(self) -> None:
        data = {"commands": [self.valid_cmd, self.valid_cmd]}
        errors = validate_registry(data, self.repo_dir)
        self.assertTrue(any("Duplicate command name" in e for e in errors))

    def test_render_claude_command(self) -> None:
        content = render_claude_command(self.valid_cmd)
        self.assertIn("description: Run test workflows", content)
        self.assertIn("Follow the instructions in the `test-skill` skill:", content)
        self.assertIn("1. Step one of instructions.", content)
        self.assertIn("$ARGUMENTS", content)

    def test_render_claude_custom_template(self) -> None:
        custom_cmd = dict(self.valid_cmd)
        custom_cmd["prompt_template"] = "Custom prompt with $ARGUMENTS"
        content = render_claude_command(custom_cmd)
        self.assertIn("Custom prompt with $ARGUMENTS", content)
        self.assertTrue(content.startswith("---"))

    def test_render_pi_extension(self) -> None:
        content = render_pi_extension(self.valid_cmd)
        self.assertIn('pi.registerCommand("test"', content)
        self.assertIn("/skill:test-skill", content)
        self.assertIn("Test Command task queued as follow-up", content)

    def test_render_pi_prompt(self) -> None:
        content = render_pi_prompt(self.valid_cmd)
        self.assertIn("description: Run test workflows", content)
        self.assertIn("Follow the `test-skill` skill to handle this task:", content)
        self.assertIn("{{args}}", content)

    def test_render_antigravity_alias(self) -> None:
        content = render_antigravity_alias(self.valid_cmd)
        self.assertIn("name: test", content)
        self.assertIn("# Test Command (/test)", content)
        self.assertIn(
            "1. Follow all instructions and guidelines in [`test-skill`](../test-skill/SKILL.md).",
            content,
        )
        self.assertIn("2. Step one of instructions.", content)

    def test_full_generation_and_check_cycle(self) -> None:
        config_path = self.repo_dir / "commands.json"
        config_path.write_text(
            json.dumps({"commands": [self.valid_cmd]}), encoding="utf-8"
        )

        # 1. Generate artifacts
        res = generate_artifacts(config_path, self.repo_dir, check=False)
        self.assertEqual(res, 0)

        # Check files exist
        self.assertTrue((self.repo_dir / "commands" / "claude" / "test.md").is_file())
        self.assertTrue(
            (
                self.repo_dir / "commands" / "pi" / "extensions" / "test-command.ts"
            ).is_file()
        )
        self.assertTrue(
            (self.repo_dir / "commands" / "pi" / "prompts" / "test.md").is_file()
        )
        # Alias skills must never be written into the shared skills tree
        self.assertFalse((self.repo_dir / "skills" / "test").exists())

        # 2. Check mode should succeed
        res_check = generate_artifacts(config_path, self.repo_dir, check=True)
        self.assertEqual(res_check, 0)

        # 3. Modify a file to simulate drift
        (self.repo_dir / "commands" / "claude" / "test.md").write_text(
            "drifted", encoding="utf-8"
        )
        res_drift = generate_artifacts(config_path, self.repo_dir, check=True)
        self.assertEqual(res_drift, 1)

        # 4. Re-sync
        res_resync = generate_artifacts(config_path, self.repo_dir, check=False)
        self.assertEqual(res_resync, 0)
        self.assertEqual(generate_artifacts(config_path, self.repo_dir, check=True), 0)


class TestInstallAntigravityAliases(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.repo_dir = root / "repo"
        self.target = root / "home" / ".gemini" / "skills"
        for name in ("test-skill", "other-skill"):
            d = self.repo_dir / "skills" / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: d\n---\n", encoding="utf-8"
            )
        self.data = {
            "commands": [
                {
                    "name": "test",
                    "skill": "test-skill",
                    "description": "Run test workflows",
                },
                {
                    "name": "other-skill",  # same name as skill: no alias
                    "skill": "other-skill",
                    "description": "Same",
                },
                {
                    "name": "optout",
                    "skill": "test-skill",
                    "description": "No alias",
                    "alias_skill": False,
                },
            ]
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_writes_only_aliases_outside_repo(self) -> None:
        install_antigravity_aliases(self.data, self.repo_dir, self.target)
        self.assertEqual([p.name for p in self.target.iterdir()], ["test"])
        alias = self.target / "test" / "SKILL.md"
        self.assertTrue(alias.is_file())
        self.assertIn(ALIAS_MARKER, alias.read_text(encoding="utf-8"))
        self.assertFalse((self.target / "optout").exists())
        # repo untouched
        self.assertFalse((self.repo_dir / "skills" / "test").exists())

    def test_idempotent(self) -> None:
        install_antigravity_aliases(self.data, self.repo_dir, self.target)
        before = sorted(p.name for p in self.target.iterdir())
        install_antigravity_aliases(self.data, self.repo_dir, self.target)
        self.assertEqual(before, sorted(p.name for p in self.target.iterdir()))

    def test_replaces_legacy_symlink_to_repo_skills(self) -> None:
        self.target.parent.mkdir(parents=True)
        self.target.symlink_to(self.repo_dir / "skills")
        install_antigravity_aliases(self.data, self.repo_dir, self.target)
        self.assertFalse(self.target.is_symlink())
        self.assertTrue(self.target.is_dir())
        self.assertFalse((self.repo_dir / "skills" / "test").exists())

    def test_removes_orphan_generated_aliases_only(self) -> None:
        install_antigravity_aliases(self.data, self.repo_dir, self.target)
        stale = self.target / "gone"
        stale.mkdir()
        (stale / "SKILL.md").write_text(f"x\n{ALIAS_MARKER}\n", encoding="utf-8")
        user = self.target / "mine"
        user.mkdir()
        (user / "SKILL.md").write_text("hand-written", encoding="utf-8")
        install_antigravity_aliases(self.data, self.repo_dir, self.target)
        self.assertFalse(stale.exists())
        self.assertTrue(user.exists())

    def test_alias_does_not_clobber_real_skill(self) -> None:
        self.data["commands"].append(
            {"name": "test-skill", "skill": "other-skill", "description": "clash"}
        )
        install_antigravity_aliases(self.data, self.repo_dir, self.target)
        self.assertFalse((self.target / "test-skill").exists())


if __name__ == "__main__":
    unittest.main()
