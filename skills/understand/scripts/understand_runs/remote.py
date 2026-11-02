# pyright: reportMissingImports=false
"""Git remote discovery and bi-directional dual navigation link generator (ADR-0005).

Provides deterministic resolution of git remote URLs into commit-pinned
GitHub/GitLab web anchors alongside primary offline local source views.
"""

from __future__ import annotations

import configparser
import contextlib
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import urllib.parse


@dataclass(frozen=True)
class RemoteInfo:
    """Parsed git remote web metadata pinned to an optional commit."""

    web_base: str
    commit: str | None = None
    host: str = "github"

    def file_link(self, file_path: str, line: int | None = None) -> str:
        """Generates canonical commit-pinned web URL for this remote."""
        clean_path = file_path.strip().lstrip("/.")
        commit_ref = self.commit or "HEAD"
        if self.host == "gitlab":
            url = f"{self.web_base}/-/blob/{commit_ref}/{clean_path}"
        else:
            url = f"{self.web_base}/blob/{commit_ref}/{clean_path}"
        if line is not None and line > 0:
            url = f"{url}#L{line}"
        return url


def parse_remote_url(raw_url: str, commit: str | None = None) -> RemoteInfo | None:
    """Parses SSH, HTTPS, or git URLs into RemoteInfo with canonical web_base and host."""
    if not raw_url:
        return None

    url = raw_url.strip()
    if not url:
        return None

    host_name = ""
    path_name = ""

    # SCP-like SSH syntax: [user@]host.com:org/repo[.git]
    if (
        "@" in url
        and ":" in url
        and not url.startswith("http://")
        and not url.startswith("https://")
        and not url.startswith("ssh://")
    ):
        _, _, after_at = url.partition("@")
        host_part, _, path_part = after_at.partition(":")
        host_name = host_part.strip()
        path_name = path_part.strip()
    elif url.startswith("ssh://"):
        rest = url[len("ssh://") :]
        if "@" in rest:
            _, _, rest = rest.partition("@")
        if "/" in rest:
            host_part, _, path_part = rest.partition("/")
            host_name = host_part.split(":")[0].strip()
            path_name = path_part.strip()
    elif url.startswith("http://") or url.startswith("https://") or url.startswith("git://"):
        parsed = urllib.parse.urlsplit(url)
        host_name = parsed.hostname or ""
        path_name = parsed.path.lstrip("/")
    elif "/" in url:
        host_part, _, path_part = url.partition("/")
        host_name = host_part.strip()
        path_name = path_part.strip()
    else:
        return None

    if not host_name or not path_name:
        return None

    # Sanitize path_name: strip trailing .git and slashes
    path_name = re.sub(r"\.git/?$", "", path_name).strip("/")
    if not path_name:
        return None

    host_lower = host_name.lower()
    if "gitlab" in host_lower:
        host_kind = "gitlab"
    elif "github" in host_lower:
        host_kind = "github"
    else:
        host_kind = host_lower.split(".")[0] if "." in host_lower else host_lower

    web_base = f"https://{host_name}/{path_name}"
    return RemoteInfo(web_base=web_base, commit=commit, host=host_kind)


def resolve_remote_web_url(
    repo_path: Path | str, commit: str | None = None
) -> RemoteInfo | None:
    """Inspects git remote `origin` and returns RemoteInfo, or None gracefully."""
    path = Path(repo_path).resolve()
    target_dir = path if path.is_dir() else path.parent
    if not target_dir.exists():
        return None

    raw_url = ""

    # 1. Inspect git remote get-url origin
    with contextlib.suppress(subprocess.SubprocessError, OSError):
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            raw_url = res.stdout.strip()

    # 2. Fallback to git config --get remote.origin.url
    if not raw_url:
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            res_cfg = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if res_cfg.returncode == 0 and res_cfg.stdout.strip():
                raw_url = res_cfg.stdout.strip()

    # 3. Direct .git/config inspection fallback (e.g. for offline/mock environments)
    if not raw_url:
        config_path = target_dir / ".git" / "config"
        if not config_path.is_file() and (target_dir / ".git").is_file():
            gitdir_content = (target_dir / ".git").read_text(encoding="utf-8", errors="replace").strip()
            if gitdir_content.startswith("gitdir:"):
                gitdir_path = (target_dir / gitdir_content[len("gitdir:") :].strip()).resolve()
                config_path = gitdir_path / "config"
        if config_path.is_file():
            with contextlib.suppress(Exception):
                cfg = configparser.ConfigParser()
                cfg.read(config_path)
                for section in cfg.sections():
                    clean_sec = section.replace('"', "").strip()
                    if clean_sec == "remote origin":
                        raw_url = cfg.get(section, "url", fallback="").strip()
                        if raw_url:
                            break

    if not raw_url:
        return None

    # Resolve commit if not passed
    if commit is None:
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            res_c = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if res_c.returncode == 0 and res_c.stdout.strip():
                commit = res_c.stdout.strip()

    return parse_remote_url(raw_url, commit=commit)


def build_file_link(
    remote_info: RemoteInfo | None, file_path: str, line: int | None = None
) -> str | None:
    """Generates canonical commit-pinned web URLs for GitHub or GitLab."""
    if remote_info is None or not file_path:
        return None
    return remote_info.file_link(file_path, line)


def format_file_citation(
    file_path: str,
    line: int | None = None,
    remote_info: RemoteInfo | None = None,
    label: str | None = None,
) -> str:
    """Formats Markdown source citation with primary offline link and secondary remote badge."""
    clean_path = file_path.strip().lstrip("/.")
    display_label = label or f"`{clean_path}`"
    offline_href = f"src/{clean_path}.html#L{line}" if line is not None else f"src/{clean_path}.html"
    primary = f"[{display_label}]({offline_href})"

    if remote_info is not None:
        remote_url = build_file_link(remote_info, clean_path, line)
        if remote_url:
            return f"{primary} [view online ↗]({remote_url})"

    return primary


__all__ = [
    "RemoteInfo",
    "build_file_link",
    "format_file_citation",
    "parse_remote_url",
    "resolve_remote_web_url",
]
