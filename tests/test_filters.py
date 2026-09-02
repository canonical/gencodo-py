# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for the built-in Jinja2 filters."""

from __future__ import annotations

import pytest

from gencodo import BUILTIN_FILTERS
from gencodo._jinja_env import _make_jinja_env


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("{{ 'My App  sub-cmd!' | slug }}", "my-app-sub-cmd"),
        ("{{ 'ref_my app' | anchor }}", "ref_my-app"),
        ("{{ 'list all iTems' | title_case }}", "List All ITems"),
        ("{{ 'app sub' | trim_prefix('app ') }}", "sub"),
        ("{{ 'app sub' | trim_prefix('zzz') }}", "app sub"),
        ("{{ 'Short.' | trim_suffix('.') }}", "Short"),
        ("{{ 'Short' | trim_suffix('') }}", "Short"),
        ("{{ 'a b c' | replace_spaces }}", "a_b_c"),
        ("{{ 'a b' | replace_spaces('-') }}", "a-b"),
        ("{{ '-' | repeat(3) }}", "---"),
        ("{{ 'x\\ny' | indent(2) }}", "  x\n  y"),
        ("{{ 'x\\ny' | indent(2, first=False) }}", "x\n  y"),
        ("{{ 'Ab' | lower }}{{ 'Ab' | upper }}", "abAB"),
    ],
)
def test_builtin_filters(template, expected):
    env = _make_jinja_env()
    assert env.from_string(template).render() == expected


def test_builtin_filters_are_registered():
    env = _make_jinja_env()
    for name in BUILTIN_FILTERS:
        assert name in env.filters


def test_extra_filters_override_builtins():
    env = _make_jinja_env({"slug": lambda _: "custom", "shout": lambda s: s + "!"})
    assert env.from_string("{{ 'x' | slug }} {{ 'hi' | shout }}").render() == "custom hi!"
