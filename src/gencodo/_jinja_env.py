# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Jinja2 environment configuration for gencodo."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from jinja2 import Environment, StrictUndefined
from jinja2.filters import do_indent

Filters = Mapping[str, Callable[..., Any]]
"""Extra Jinja2 filters, as accepted by the ``extra_filters`` parameters."""


def _indent(s: str, width: int = 4, *, first: bool = True, blank: bool = False) -> str:
    """Indent every line of *s* by *width* spaces.

    Unlike Jinja's built-in ``indent``, the first line is indented too by
    default (``first=True``), which suits values placed at the start of a line.
    Pass ``first=False`` when the template already indents the first line.
    """
    return do_indent(s, width=width, first=first, blank=blank)


def _repeat(s: str, n: int) -> str:
    """Repeat *s* *n* times (``'=' | repeat(heading_len)``)."""
    return s * n


def _slugify(s: str, *, keep_underscore: bool) -> str:
    pattern = r"[^a-z0-9_]+" if keep_underscore else r"[^a-z0-9]+"
    return re.sub(pattern, "-", s.lower()).strip("-")


def _slug(s: str) -> str:
    """Lowercase, non-alphanumerics to dashes, trimmed: ``"My App sub" -> "my-app-sub"``."""
    return _slugify(s, keep_underscore=False)


def _anchor(s: str) -> str:
    """Like :func:`_slug` but keeps underscores: ``"ref_my app" -> "ref_my-app"``."""
    return _slugify(s, keep_underscore=True)


def _title_case(s: str) -> str:
    """Upper-case the first letter of every word, leaving the rest untouched."""
    return " ".join(w[:1].upper() + w[1:] for w in s.split(" "))


def _trim_prefix(s: str, prefix: str) -> str:
    """Remove *prefix* from the start of *s* if present."""
    return s[len(prefix) :] if prefix and s.startswith(prefix) else s


def _trim_suffix(s: str, suffix: str) -> str:
    """Remove *suffix* from the end of *s* if present."""
    return s[: -len(suffix)] if suffix and s.endswith(suffix) else s


def _replace_spaces(s: str, replacement: str = "_") -> str:
    """Replace spaces with *replacement* (default ``_``), e.g. for reference labels."""
    return s.replace(" ", replacement)


BUILTIN_FILTERS: Filters = {
    "indent": _indent,
    "repeat": _repeat,
    "slug": _slug,
    "anchor": _anchor,
    "title_case": _title_case,
    "trim_prefix": _trim_prefix,
    "trim_suffix": _trim_suffix,
    "replace_spaces": _replace_spaces,
}
"""Filters gencodo adds on top of Jinja2's defaults."""


def _make_jinja_env(extra_filters: Filters | None = None) -> Environment:
    """Create a configured Jinja2 Environment for documentation generation.

    Args:
        extra_filters: Additional filters; names that clash with
            :data:`BUILTIN_FILTERS` override them.

    Returns:
        A Jinja2 Environment with ``StrictUndefined`` (unknown names fail
        rendering) and gencodo's filters installed.
    """
    env = Environment(
        autoescape=False,  # noqa: S701  # nosec B701 - outputs Markdown/reST, not HTML
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters.update(BUILTIN_FILTERS)
    if extra_filters:
        env.filters.update(extra_filters)
    return env
