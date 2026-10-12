#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate slash command artifacts across agent runtimes from commands.json.

Target runtimes:
- Claude Code: commands/claude/<name>.md
- Pi Extensions: commands/pi/extensions/<name>-command.ts
- Pi Prompts: commands/pi/prompts/<name>.md
- Antigravity / Gemini: alias skills installed into the user's agent config
  (default ~/.gemini/config/skills) via --install-antigravity; never written to the repo
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

ALIAS_MARKER = "<!-- generated:alias-skill -->"


def format_instruction_item(item: str, index: int) -> str:
    """Format an instruction string with appropriate numbering and sub-indentation."""
    item = item.strip()
    sub_lines = item.splitlines()
    if not sub_lines:
        return ""
    first_line = sub_lines[0].lstrip("0123456789.- ")
    lines = [f"{index}. {first_line}"]
    for sub in sub_lines[1:]:
        stripped = sub.strip()
        if stripped:
            lines.append(f"   {stripped}")
        else:
            lines.append("")
    return "\n".join(lines)


def format_instructions_list(
    instructions: list[str] | str, start_index: int = 1
) -> str:
    """Format instructions into a numbered markdown list."""
    if isinstance(instructions, str):
        instructions = [instructions]

    formatted_items = []
    idx = start_index
    for item in instructions:
        formatted = format_instruction_item(item, idx)
        if formatted:
            formatted_items.append(formatted)
            idx += 1
    return "\n".join(formatted_items)


def render_claude_command(cmd: dict[str, Any]) -> str:
    """Render the Claude Code command markdown file."""
    if "prompt_template" in cmd and cmd["prompt_template"]:
        template = cmd["prompt_template"].strip()
        if not template.startswith("---"):
            template = f"---\ndescription: {cmd['description']}\n---\n\n{template}"
        return f"{template}\n"

    description = cmd["description"].strip()
    skill = cmd["skill"].strip()
    instructions = cmd.get("instructions", [])

    if instructions:
        body = (
            f"You are tasked with: {description}.\n\n"
            f"Follow the instructions in the `{skill}` skill:\n"
            f"{format_instructions_list(instructions, start_index=1)}\n\n"
            "User request:\n"
            "$ARGUMENTS\n"
        )
    else:
        body = (
            f"You are tasked with: {description}.\n\n"
            f"Follow all instructions and workflows in the `{skill}` skill.\n\n"
            "User request:\n"
            "$ARGUMENTS\n"
        )

    return f"---\ndescription: {description}\n---\n\n{body}"


def render_pi_extension(cmd: dict[str, Any]) -> str:
    """Render the Pi extension TypeScript file."""
    name = cmd["name"].strip()
    skill = cmd["skill"].strip()
    title = cmd.get("title", name).strip()
    description = cmd["description"].strip()
    default_action = cmd.get("default_action", f"using the {skill} skill").strip()

    # Escape quotes for JS/TS string literals
    esc_desc = description.replace('"', '\\"')
    esc_action = default_action.replace('"', '\\"')
    esc_title = title.replace('"', '\\"')

    return f"""/**
 * {title} Command Extension for Pi
 * Registers `/{name}` to {description.lower()}.
 */
import type {{ ExtensionAPI }} from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {{
  pi.registerCommand("{name}", {{
    description: "{esc_desc}",
    handler: async (args, ctx) => {{
      const query = args.trim();
      const message = query
        ? `/skill:{skill} ${{query}}`
        : "/skill:{skill} Please assist with {esc_action}.";

      if (!ctx.isIdle()) {{
        pi.sendUserMessage(message, {{ deliverAs: "followUp" }});
        ctx.ui.notify("{esc_title} task queued as follow-up", "info");
      }} else {{
        pi.sendUserMessage(message);
      }}
    }},
  }});
}}
"""


def render_pi_prompt(cmd: dict[str, Any]) -> str:
    """Render the Pi prompt template markdown file."""
    description = cmd["description"].strip()
    skill = cmd["skill"].strip()

    return f"""---
description: {description}
---

Follow the `{skill}` skill to handle this task:

{{{{args}}}}
"""


def render_antigravity_alias(cmd: dict[str, Any]) -> str:
    """Render an Antigravity alias skill (skills/<name>/SKILL.md)."""
    name = cmd["name"].strip()
    skill = cmd["skill"].strip()
    title = cmd.get("title", name).strip()
    description = cmd["description"].strip()
    instructions = cmd.get("instructions", [])

    lines = [
        "---",
        f"name: {name}",
        f"description: {description}. Short command alias for {skill}.",
        "---",
        "",
        f"# {title} (/{name})",
        "",
        f"{ALIAS_MARKER}",
        f"When invoked, load and execute the **`{skill}`** skill:",
        f"1. Follow all instructions and guidelines in [`{skill}`](../{skill}/SKILL.md).",
    ]

    if instructions:
        formatted = format_instructions_list(instructions, start_index=2)
        if formatted:
            lines.append(formatted)

    return "\n".join(lines) + "\n"


def validate_registry(data: dict[str, Any], repo_dir: Path) -> list[str]:
    """Validate commands.json entries and ensure backing skills exist."""
    errors: list[str] = []
    if "commands" not in data or not isinstance(data["commands"], list):
        return ["'commands' array is required in registry."]

    seen_names: set[str] = set()
    for idx, cmd in enumerate(data["commands"]):
        if not isinstance(cmd, dict):
            errors.append(f"Command at index {idx} must be an object.")
            continue

        name = cmd.get("name")
        if not name or not isinstance(name, str):
            errors.append(f"Command at index {idx} is missing 'name'.")
            continue

        if not re.match(r"^[a-z0-9-]+$", name):
            errors.append(
                f"Command '{name}' has invalid name. Must be lowercase alphanumeric with hyphens."
            )

        if name in seen_names:
            errors.append(f"Duplicate command name '{name}'.")
        seen_names.add(name)

        skill = cmd.get("skill")
        if not skill or not isinstance(skill, str):
            errors.append(f"Command '{name}' is missing 'skill'.")
        else:
            skill_file = repo_dir / "skills" / skill / "SKILL.md"
            if not skill_file.is_file():
                errors.append(
                    f"Command '{name}' references backing skill '{skill}', but {skill_file} does not exist."
                )

        if "description" not in cmd or not isinstance(cmd["description"], str):
            errors.append(f"Command '{name}' is missing 'description'.")

    return errors


def generate_artifacts(
    config_path: Path, repo_dir: Path, check: bool = False, clean: bool = False
) -> int:
    """Generate or check all command artifacts."""
    if not config_path.is_file():
        print(f"Error: Config file {config_path} not found.", file=sys.stderr)
        return 1

    with open(config_path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as err:
            print(f"Error parsing JSON in {config_path}: {err}", file=sys.stderr)
            return 1

    errors = validate_registry(data, repo_dir)
    if errors:
        print("Registry validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  ❌ {err}", file=sys.stderr)
        return 1

    expected_files: dict[Path, str] = {}
    expected_command_names: set[str] = set()

    for cmd in data["commands"]:
        name = cmd["name"]
        expected_command_names.add(name)

        # 1. Claude Code command
        claude_path = repo_dir / "commands" / "claude" / f"{name}.md"
        expected_files[claude_path] = render_claude_command(cmd)

        # 2. Pi Extension
        pi_ext_path = repo_dir / "commands" / "pi" / "extensions" / f"{name}-command.ts"
        expected_files[pi_ext_path] = render_pi_extension(cmd)

        # 3. Pi Prompt
        pi_prompt_path = repo_dir / "commands" / "pi" / "prompts" / f"{name}.md"
        expected_files[pi_prompt_path] = render_pi_prompt(cmd)

    drift_detected = False

    if check:
        for path, expected_content in expected_files.items():
            if not path.is_file():
                print(f"❌ Missing artifact: {path.relative_to(repo_dir)}")
                drift_detected = True
                continue
            current_content = path.read_text(encoding="utf-8")
            if current_content != expected_content:
                print(f"❌ Drift detected in: {path.relative_to(repo_dir)}")
                drift_detected = True

        if drift_detected:
            print(
                "\nRun 'make install' or 'uv run tools/generate_commands.py' to synchronize."
            )
            return 1

        print("✅ All slash command artifacts are up-to-date.")
        return 0

    # Write mode
    created_count = 0
    updated_count = 0
    unchanged_count = 0

    for path, content in expected_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file():
            path.write_text(content, encoding="utf-8")
            print(f"  + Created {path.relative_to(repo_dir)}")
            created_count += 1
        else:
            current = path.read_text(encoding="utf-8")
            if current != content:
                path.write_text(content, encoding="utf-8")
                print(f"  ~ Updated {path.relative_to(repo_dir)}")
                updated_count += 1
            else:
                unchanged_count += 1

    print(
        f"\nSlash command compilation complete: {created_count} created, {updated_count} updated, {unchanged_count} unchanged."
    )

    if clean:
        clean_orphans(repo_dir, expected_command_names)

    return 0


def clean_orphans(repo_dir: Path, valid_names: set[str]) -> None:
    """Clean orphan command files not defined in commands.json."""
    # 1. Claude
    claude_dir = repo_dir / "commands" / "claude"
    if claude_dir.is_dir():
        for f in claude_dir.glob("*.md"):
            if f.stem not in valid_names:
                f.unlink()
                print(f"  - Removed orphan Claude command: {f.relative_to(repo_dir)}")

    # 2. Pi Extensions
    pi_ext_dir = repo_dir / "commands" / "pi" / "extensions"
    if pi_ext_dir.is_dir():
        for f in pi_ext_dir.glob("*-command.ts"):
            name = f.name.replace("-command.ts", "")
            if name not in valid_names:
                f.unlink()
                print(f"  - Removed orphan Pi extension: {f.relative_to(repo_dir)}")

    # 3. Pi Prompts
    pi_prompt_dir = repo_dir / "commands" / "pi" / "prompts"
    if pi_prompt_dir.is_dir():
        for f in pi_prompt_dir.glob("*.md"):
            if f.stem not in valid_names:
                f.unlink()
                print(f"  - Removed orphan Pi prompt: {f.relative_to(repo_dir)}")


def wants_alias(cmd: dict[str, Any]) -> bool:
    """Whether a command needs an Antigravity alias skill."""
    return bool(cmd.get("alias_skill", True)) and cmd["name"] != cmd["skill"]


def _is_generated_alias(path: Path) -> bool:
    skill_md = path / "SKILL.md"
    if path.is_symlink() or not skill_md.is_file():
        return False
    return ALIAS_MARKER in skill_md.read_text(encoding="utf-8")


def _remove_generated(path: Path) -> None:
    (path / "SKILL.md").unlink()
    path.rmdir()


def install_antigravity_aliases(
    data: dict[str, Any], repo_dir: Path, target: Path
) -> None:
    """Write generated alias skills into a real directory outside the repo.

    Aliases carry ALIAS_MARKER. A legacy symlink at target (e.g. to the repo
    skills dir) is replaced by a real directory. Orphan generated aliases are
    removed; anything else already in the target is left alone.
    """
    skills_src = repo_dir / "skills"
    if target.is_symlink():
        target.unlink()
    target.mkdir(parents=True, exist_ok=True)

    skill_names = {p.name for p in skills_src.iterdir() if p.is_dir()}
    wanted: dict[str, dict[str, Any]] = {}
    for cmd in data["commands"]:
        if not wants_alias(cmd):
            continue
        if cmd["name"] in skill_names:
            print(f"  ! Skipping alias {cmd['name']}: a real skill has that name")
            continue
        wanted[cmd["name"]] = cmd

    for name, cmd in wanted.items():
        alias_dir = target / name
        if alias_dir.exists() and not _is_generated_alias(alias_dir):
            print(f"  ! Skipping alias {name}: non-generated entry exists")
            continue
        alias_dir.mkdir(exist_ok=True)
        (alias_dir / "SKILL.md").write_text(
            render_antigravity_alias(cmd), encoding="utf-8"
        )

    for entry in target.iterdir():
        if entry.name not in wanted and _is_generated_alias(entry):
            _remove_generated(entry)
            print(f"  - Removed orphan alias skill: {entry}")


def uninstall_antigravity_aliases(target: Path) -> None:
    """Remove generated alias skills from the target dir."""
    if not target.is_dir() or target.is_symlink():
        return
    for entry in target.iterdir():
        if _is_generated_alias(entry):
            _remove_generated(entry)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate slash commands for Claude, Pi, and Antigravity."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("commands.json"),
        help="Path to commands.json registry (default: commands.json)",
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=Path("."),
        help="Path to repository root (default: current directory)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify if generated artifacts match without writing (drift check)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove orphaned command artifacts not defined in commands.json",
    )

    parser.add_argument(
        "--install-antigravity",
        nargs="?",
        const=str(Path.home() / ".gemini" / "config" / "skills"),
        metavar="DIR",
        help="Write alias skills into DIR (default ~/.gemini/config/skills)",
    )
    parser.add_argument(
        "--uninstall-antigravity",
        nargs="?",
        const=str(Path.home() / ".gemini" / "config" / "skills"),
        metavar="DIR",
        help="Remove generated alias skills from DIR",
    )

    args = parser.parse_args()
    repo_dir = args.repo_dir.resolve()
    config_path = (
        (repo_dir / args.config).resolve()
        if not args.config.is_absolute()
        else args.config
    )

    if args.uninstall_antigravity:
        uninstall_antigravity_aliases(Path(args.uninstall_antigravity))
        return 0

    rc = generate_artifacts(config_path, repo_dir, check=args.check, clean=args.clean)
    if rc == 0 and args.install_antigravity and not args.check:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        install_antigravity_aliases(data, repo_dir, Path(args.install_antigravity))
    return rc


if __name__ == "__main__":
    sys.exit(main())
