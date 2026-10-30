"""Unit tests for assets/tokens.css: Material 3 roles, light and dark, no component rules."""
import re
from pathlib import Path

import pytest

TOKENS = re.sub(
    r"/\*.*?\*/", "",
    (Path(__file__).resolve().parents[2] / "assets" / "tokens.css").read_text(encoding="utf-8"),
    flags=re.S,
)

COLOUR_ROLES = [
    "primary", "on-primary", "primary-container", "on-primary-container",
    "secondary", "on-secondary", "secondary-container", "on-secondary-container",
    "tertiary", "on-tertiary", "tertiary-container", "on-tertiary-container",
    "error", "on-error", "error-container", "on-error-container",
    "background", "on-background",
    "surface", "on-surface", "surface-variant", "on-surface-variant",
    "surface-container-lowest", "surface-container-low", "surface-container",
    "surface-container-high", "surface-container-highest",
    "outline", "outline-variant",
    "inverse-surface", "inverse-on-surface", "inverse-primary",
    "shadow", "scrim",
]


def declared_in(selector_pattern):
    """The custom properties declared in every block whose selector matches."""
    names = set()
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", TOKENS):
        if re.search(selector_pattern, selector):
            names |= set(re.findall(r"--([\w-]+)\s*:", body))
    return names


@pytest.mark.parametrize("role", COLOUR_ROLES)
def test_light_scheme_defines_the_role(role):
    assert f"md-sys-color-{role}" in declared_in(r"^\s*:root\s*$")


@pytest.mark.parametrize("role", COLOUR_ROLES)
def test_dark_scheme_redefines_the_role(role):
    assert f"md-sys-color-{role}" in declared_in(r'data-theme="dark"')


def test_explicit_light_override_exists_for_readers_with_a_dark_system():
    assert "md-sys-color-surface" in declared_in(r'data-theme="light"')


def test_dark_system_preference_is_honoured():
    assert re.search(r"@media\s*\(prefers-color-scheme:\s*dark\)", TOKENS)


@pytest.mark.parametrize("token", [
    "md-sys-typescale-body-font", "md-sys-typescale-display-font", "md-sys-typescale-code-font",
    "md-sys-shape-corner-small", "md-sys-shape-corner-medium", "md-sys-shape-corner-large",
    "md-sys-elevation-1",
])
def test_type_shape_and_elevation_tokens_exist(token):
    assert token in declared_in(r"^\s*:root\s*$")


def test_token_file_has_no_component_rules_so_other_skills_can_adopt_it():
    selectors = [s.strip() for s in re.findall(r"([^{}@]+)\{", re.sub(r"@media[^{]*\{", "", TOKENS))]
    assert all(s.startswith(":root") for s in selectors), selectors


def test_token_file_loads_no_font_or_remote_resource():
    assert "@font-face" not in TOKENS and "url(" not in TOKENS and "@import" not in TOKENS
