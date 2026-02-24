"""Jinja2 environment configuration for gencodo."""

from __future__ import annotations

from jinja2 import Environment, StrictUndefined
from jinja2.filters import do_indent


def _make_jinja_env() -> Environment:
    """Create a configured Jinja2 Environment for documentation generation.

    Returns:
        A Jinja2 Environment with custom filters for documentation rendering.
    """
    env = Environment(
        autoescape=False,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    def _indent(s: str, width: int = 4, *, blank: bool = False) -> str:
        return do_indent(s, width=width, first=True, blank=blank)

    def _repeat(s: str, n: int) -> str:
        return s * n

    env.filters["indent"] = _indent
    env.filters["repeat"] = _repeat
    return env
