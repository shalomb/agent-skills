# Agent Skills: install skills and slash commands into each agent runtime.
# Everything is symlinked to this checkout by absolute path, so re-running
# `make install` from a new clone location repoints every link.

SHELL := /usr/bin/env bash
REPO_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SKILLS_SRC := $(REPO_DIR)/skills

# Agents whose skills directory is a symlink to $(SKILLS_SRC)
SKILL_LINKS := $(HOME)/.pi/agent/skills $(HOME)/.claude/skills $(HOME)/.gemini/skills

# Slash command locations: <repo source dir>:<glob>:<target dir>
CLAUDE_CMDS := $(HOME)/.claude/commands
PI_EXTS := $(HOME)/.pi/agent/extensions
PI_PROMPTS := $(HOME)/.pi/agent/prompts
# Generated Antigravity alias skills (real directory, kept out of the repo)
ALIAS_DIR := $(HOME)/.gemini/config/skills

SKILLS_CONF := $(HOME)/.config/agent-skills/skills.conf

# link SRC DEST: idempotent; repoints an existing symlink, backs up a real dir
define link
if [ -d "$(2)" ] && [ ! -L "$(2)" ]; then mv "$(2)" "$(2).bak"; echo "  ! backed up $(2) -> $(2).bak"; fi; \
mkdir -p "$$(dirname "$(2)")"; ln -sfn "$(1)" "$(2)"; echo "  ✓ $(2) -> $(1)"
endef

.PHONY: help install uninstall status test

help:
	@echo "make install    Compile commands, then symlink skills and commands into every agent"
	@echo "make uninstall  Remove those links and generated aliases"
	@echo "make status     Show where each link points (flags stale ones)"
	@echo "make test       Run generator unit tests and the commands.json drift check"

install:
	@uv run tools/generate_commands.py --install-antigravity "$(ALIAS_DIR)" | rg -v '^\s+[+~]|^Slash|^$$' || true
	@echo "Linking skills -> $(SKILLS_SRC)"
	@for t in $(SKILL_LINKS); do $(call link,$(SKILLS_SRC),$$t); done
	@echo "Linking slash commands"
	@for f in commands/claude/*.md; do $(call link,$(REPO_DIR)/$$f,$(CLAUDE_CMDS)/$$(basename $$f)); done
	@for f in commands/pi/extensions/*.ts; do $(call link,$(REPO_DIR)/$$f,$(PI_EXTS)/$$(basename $$f)); done
	@for f in commands/pi/prompts/*.md; do $(call link,$(REPO_DIR)/$$f,$(PI_PROMPTS)/$$(basename $$f)); done
	@echo "  ✓ Antigravity aliases -> $(ALIAS_DIR)"
	@uv tool install --editable "$(SKILLS_SRC)/todo-navigator" --force >/dev/null && echo "  ✓ todo CLI installed"
	@if [ -f "$(SKILLS_CONF)" ] && grep -q "shalomb:" "$(SKILLS_CONF)"; then \
		sed -i 's|shalomb:.*|shalomb:$(SKILLS_SRC)" )|' "$(SKILLS_CONF)"; echo "  ✓ updated $(SKILLS_CONF)"; fi

uninstall:
	@for t in $(SKILL_LINKS) $(CLAUDE_CMDS)/*.md $(PI_EXTS)/*-command.ts $(PI_PROMPTS)/*.md; do \
		if [ -L "$$t" ] && [[ "$$(readlink "$$t")" == $(REPO_DIR)/* ]]; then rm "$$t"; echo "  - $$t"; fi; \
	done
	@uv run tools/generate_commands.py --uninstall-antigravity "$(ALIAS_DIR)"
	@uv tool uninstall todo-navigator 2>/dev/null || true

status:
	@for t in $(SKILL_LINKS) $(CLAUDE_CMDS)/*.md $(PI_EXTS)/*-command.ts $(PI_PROMPTS)/*.md; do \
		[ -L "$$t" ] || continue; dest="$$(readlink "$$t")"; \
		case "$$dest" in $(REPO_DIR)/*) ok=" ";; *) ok="STALE";; esac; \
		echo "  $$ok $$t -> $$dest"; \
	done | sort
	@echo "Antigravity aliases in $(ALIAS_DIR):"
	@rg -l 'generated:alias-skill' "$(ALIAS_DIR)" 2>/dev/null | xargs -r -n1 dirname | xargs -r -n1 basename | sort | tr '\n' ' '; echo

test:
	@uv run python -m unittest tools/test_generate_commands.py 2>&1 | rg '^(Ran|OK|FAILED|ERROR|FAIL)'
	@uv run tools/generate_commands.py --check
