#!/usr/bin/env python3
"""
12-Factor Configuration Loader for Harness Tools & Skills.

Resolution order (highest to lowest priority):
1. Explicit function arguments / CLI options
2. Environment variables:
   - HARNESS_ACCOUNT_ID
   - HARNESS_API_KEY
   - HARNESS_ORG_ID
   - HARNESS_PROJECT_ID
   - HARNESS_BASE_URL (defaults to https://app.harness.io)
   - HARNESS_PROFILE (selects ~/.config/harness/<profile>)
3. Local project configuration (.harness/config.yaml or .env)
4. User profile configuration (~/.config/harness/<profile>, defaults to 'default' or single available profile)
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import yaml


@dataclass
class HarnessConfig:
    account_id: str
    api_key: str
    org_id: Optional[str] = None
    project_id: Optional[str] = None
    base_url: str = "https://app.harness.io"
    source: str = "unknown"

    def headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }


def _load_yaml_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if isinstance(content, dict) else {}
    except Exception:
        return {}


def load_harness_config(
    account_id: Optional[str] = None,
    api_key: Optional[str] = None,
    org_id: Optional[str] = None,
    project_id: Optional[str] = None,
    base_url: Optional[str] = None,
    profile: Optional[str] = None,
) -> HarnessConfig:
    """
    Resolves Harness configuration following 12-factor principles.
    """
    # 1. Determine profile name
    profile_name = profile or os.environ.get("HARNESS_PROFILE")

    # 2. Check user config file ~/.config/harness/<profile>
    config_dir = Path.home() / ".config" / "harness"
    file_cfg = {}
    config_source = "environment"

    if config_dir.exists() and config_dir.is_dir():
        if profile_name:
            target_file = config_dir / profile_name
            if target_file.is_file():
                file_cfg = _load_yaml_file(target_file)
                config_source = f"file:~/.config/harness/{profile_name}"
        else:
            # Check for 'default' or pick the first available profile
            default_file = config_dir / "default"
            if default_file.is_file():
                file_cfg = _load_yaml_file(default_file)
                config_source = "file:~/.config/harness/default"
            else:
                available = [f for f in config_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
                if len(available) == 1:
                    file_cfg = _load_yaml_file(available[0])
                    config_source = f"file:~/.config/harness/{available[0].name}"

    # 3. Resolve each value: explicit arg > ENV > file config
    resolved_account = (
        account_id
        or os.environ.get("HARNESS_ACCOUNT_ID")
        or file_cfg.get("harness_account_id")
        or file_cfg.get("account_id")
    )

    resolved_api_key = (
        api_key
        or os.environ.get("HARNESS_API_KEY")
        or file_cfg.get("harness_api_key")
        or file_cfg.get("api_key")
    )

    resolved_org = (
        org_id
        or os.environ.get("HARNESS_ORG_ID")
        or file_cfg.get("harness_org_id")
        or file_cfg.get("org_id")
    )

    resolved_project = (
        project_id
        or os.environ.get("HARNESS_PROJECT_ID")
        or file_cfg.get("harness_project_id")
        or file_cfg.get("project_id")
    )

    resolved_base_url = (
        base_url
        or os.environ.get("HARNESS_BASE_URL")
        or file_cfg.get("harness_base_url")
        or file_cfg.get("base_url")
        or "https://app.harness.io"
    )

    if not resolved_account or not resolved_api_key:
        missing = []
        if not resolved_account:
            missing.append("HARNESS_ACCOUNT_ID")
        if not resolved_api_key:
            missing.append("HARNESS_API_KEY")
        raise ValueError(
            f"Missing required Harness credentials ({', '.join(missing)}). "
            f"Set via environment variables or profile in ~/.config/harness/."
        )

    return HarnessConfig(
        account_id=str(resolved_account).strip(),
        api_key=str(resolved_api_key).strip(),
        org_id=str(resolved_org).strip() if resolved_org else None,
        project_id=str(resolved_project).strip() if resolved_project else None,
        base_url=str(resolved_base_url).strip().rstrip("/"),
        source=config_source,
    )


if __name__ == "__main__":
    try:
        cfg = load_harness_config()
        masked_key = cfg.api_key[:8] + "..." + cfg.api_key[-4:] if len(cfg.api_key) > 12 else "***"
        print("✅ Successfully resolved Harness 12-factor configuration:")
        print(f"   Source:     {cfg.source}")
        print(f"   Base URL:   {cfg.base_url}")
        print(f"   Account ID: {cfg.account_id}")
        print(f"   Org ID:     {cfg.org_id}")
        print(f"   Project ID: {cfg.project_id}")
        print(f"   API Key:    {masked_key}")
    except Exception as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
