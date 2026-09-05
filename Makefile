# Makefile for Agent Skills
# Manages symlinks and slash command propagation across agent runtimes:
# - Pi (~/.pi)
# - Antigravity / Gemini CLI (~/.gemini)
# - Claude Code (~/.claude)

SHELL := /usr/bin/env bash
REPO_DIR := $(CURDIR)
SKILLS_SRC := $(REPO_DIR)/skills

PI_DIR := $(HOME)/.pi/agent
GEMINI_DIR := $(HOME)/.gemini
GEMINI_CONFIG_DIR := $(HOME)/.gemini/config
CLAUDE_DIR := $(HOME)/.claude

CLAUDE_COMMANDS_DIR := $(CLAUDE_DIR)/commands
PI_EXTENSIONS_DIR := $(PI_DIR)/extensions
PI_PROMPTS_DIR := $(PI_DIR)/prompts

SKILLS_CONF := $(HOME)/.config/agent-skills/skills.conf

.PHONY: all help install uninstall status doctor

all: help

help:
	@echo "Agent Skills Management"
	@echo ""
	@echo "Usage:"
	@echo "  make install    Set up symlinks to this repo and register slash commands"
	@echo "  make status     Inspect current symlinks and registered commands"
	@echo "  make doctor     Run skills doctor audit"
	@echo "  make uninstall  Remove symlinks and registered commands"
	@echo ""

install: install-skills install-commands update-conf
	@echo ""
	@echo "=================================================================="
	@echo "✅ Installation complete! All skills and commands linked to:"
	@echo "   $(SKILLS_SRC)"
	@echo "=================================================================="
	@$(MAKE) --no-print-directory status

install-skills:
	@echo "Linking skills directory to agent runtimes..."
	@mkdir -p "$(PI_DIR)" "$(GEMINI_CONFIG_DIR)" "$(GEMINI_DIR)" "$(CLAUDE_DIR)"
	@# Safe link helper: replace symlink or backup existing directory
	@for target in "$(PI_DIR)/skills" "$(GEMINI_CONFIG_DIR)/skills" "$(GEMINI_DIR)/skills" "$(CLAUDE_DIR)/skills"; do \
		if [ -d "$$target" ] && [ ! -L "$$target" ]; then \
			echo "  ⚠️ Backing up existing directory $$target to $$target.bak"; \
			mv "$$target" "$$target.bak"; \
		fi; \
		ln -sfn "$(SKILLS_SRC)" "$$target"; \
		echo "  ✓ Linked $$target -> $(SKILLS_SRC)"; \
	done

install-commands:
	@echo ""
	@echo "Registering slash commands..."
	@# Claude Code commands
	@mkdir -p "$(CLAUDE_COMMANDS_DIR)"
	@if [ -d "$(REPO_DIR)/commands/claude" ]; then \
		for cmd in "$(REPO_DIR)/commands/claude"/*.md; do \
			[ -e "$$cmd" ] || continue; \
			ln -sfn "$$cmd" "$(CLAUDE_COMMANDS_DIR)/$$(basename "$$cmd")"; \
			echo "  ✓ Claude Code:  /$$([ -f "$$cmd" ] && basename "$$cmd" .md) -> $$cmd"; \
		done; \
	fi
	@# Pi Extensions
	@mkdir -p "$(PI_EXTENSIONS_DIR)"
	@if [ -d "$(REPO_DIR)/commands/pi/extensions" ]; then \
		for ext in "$(REPO_DIR)/commands/pi/extensions"/*.ts; do \
			[ -e "$$ext" ] || continue; \
			ln -sfn "$$ext" "$(PI_EXTENSIONS_DIR)/$$(basename "$$ext")"; \
			echo "  ✓ Pi Extension: /$$([ -f "$$ext" ] && basename "$$ext" -command.ts) -> $$ext"; \
		done; \
	fi
	@# Pi Prompt Templates
	@mkdir -p "$(PI_PROMPTS_DIR)"
	@if [ -d "$(REPO_DIR)/commands/pi/prompts" ]; then \
		for prm in "$(REPO_DIR)/commands/pi/prompts"/*.md; do \
			[ -e "$$prm" ] || continue; \
			ln -sfn "$$prm" "$(PI_PROMPTS_DIR)/$$(basename "$$prm")"; \
			echo "  ✓ Pi Prompt:    /prompt:$$([ -f "$$prm" ] && basename "$$prm" .md) -> $$prm"; \
		done; \
	fi
	@# Antigravity/Gemini skills (adr is linked via $(SKILLS_SRC)/adr)
	@if [ -d "$(SKILLS_SRC)/adr" ]; then \
		echo "  ✓ Antigravity:  /adr -> $(SKILLS_SRC)/adr/SKILL.md"; \
	fi

update-conf:
	@if [ -f "$(SKILLS_CONF)" ]; then \
		if grep -q "shalomb:" "$(SKILLS_CONF)"; then \
			sed -i 's|shalomb:.*|shalomb:$(SKILLS_SRC)" )|' "$(SKILLS_CONF)"; \
			echo "  ✓ Updated $(SKILLS_CONF) source 'shalomb' to $(SKILLS_SRC)"; \
		fi; \
	fi

status:
	@echo ""
	@echo "--- Skills Target Symlinks ---"
	@for target in "$(PI_DIR)/skills" "$(GEMINI_CONFIG_DIR)/skills" "$(GEMINI_DIR)/skills" "$(CLAUDE_DIR)/skills"; do \
		if [ -L "$$target" ]; then \
			echo "  $$target -> $$(readlink "$$target")"; \
		elif [ -d "$$target" ]; then \
			echo "  $$target (directory, not symlinked)"; \
		else \
			echo "  $$target (not present)"; \
		fi; \
	done
	@echo ""
	@echo "--- Registered Slash Commands ---"
	@echo "Claude Code (~/.claude/commands):"
	@if [ -d "$(CLAUDE_COMMANDS_DIR)" ]; then \
		find "$(CLAUDE_COMMANDS_DIR)" -maxdepth 1 -type l -exec ls -l {} + | awk '{print "  " $$9 " -> " $$11}'; \
	fi
	@echo "Pi Extensions (~/.pi/agent/extensions):"
	@if [ -d "$(PI_EXTENSIONS_DIR)" ]; then \
		find "$(PI_EXTENSIONS_DIR)" -maxdepth 1 -type l -exec ls -l {} + | awk '{print "  " $$9 " -> " $$11}'; \
	fi
	@echo "Pi Prompts (~/.pi/agent/prompts):"
	@if [ -d "$(PI_PROMPTS_DIR)" ]; then \
		find "$(PI_PROMPTS_DIR)" -maxdepth 1 -type l -exec ls -l {} + | awk '{print "  " $$9 " -> " $$11}'; \
	fi
	@echo "Antigravity Skills (~/.gemini/skills):"
	@if [ -d "$(GEMINI_DIR)/skills/adr" ]; then \
		echo "  /adr available via $(GEMINI_DIR)/skills/adr"; \
	fi

doctor:
	@if [ -x "$(REPO_DIR)/tools/skills" ]; then \
		"$(REPO_DIR)/tools/skills" doctor || true; \
	else \
		echo "tools/skills not found or not executable"; \
	fi

uninstall:
	@echo "Removing agent skills symlinks and commands..."
	@rm -f "$(PI_DIR)/skills" "$(GEMINI_CONFIG_DIR)/skills" "$(GEMINI_DIR)/skills" "$(CLAUDE_DIR)/skills"
	@if [ -d "$(REPO_DIR)/commands/claude" ]; then \
		for cmd in "$(REPO_DIR)/commands/claude"/*.md; do \
			rm -f "$(CLAUDE_COMMANDS_DIR)/$$(basename "$$cmd")"; \
		done; \
	fi
	@if [ -d "$(REPO_DIR)/commands/pi/extensions" ]; then \
		for ext in "$(REPO_DIR)/commands/pi/extensions"/*.ts; do \
			rm -f "$(PI_EXTENSIONS_DIR)/$$(basename "$$ext")"; \
		done; \
	fi
	@if [ -d "$(REPO_DIR)/commands/pi/prompts" ]; then \
		for prm in "$(REPO_DIR)/commands/pi/prompts"/*.md; do \
			rm -f "$(PI_PROMPTS_DIR)/$$(basename "$$prm")"; \
		done; \
	fi
	@echo "Uninstalled."
