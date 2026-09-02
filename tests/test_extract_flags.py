# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for _extract_flags."""

from gencodo._core import _extract_flags
from tests.conftest import (
    FarewellCommand,
    GreetCommand,
    HelloCommand,
    NoArgCommand,
    SuppressedFlagCommand,
)


def test_extract_flags_with_flags():
    flags = _extract_flags(GreetCommand)
    names = [f.name for f in flags]
    assert "--formal" in names
    assert "--enthusiasm" in names
    assert "--suffix" in names


def test_extract_flags_skips_positionals():
    flags = _extract_flags(GreetCommand)
    names = [f.name for f in flags]
    assert "name" not in names


def test_extract_flags_no_flags():
    flags = _extract_flags(HelloCommand)
    assert flags == []


def test_extract_flags_suppressed():
    flags = _extract_flags(SuppressedFlagCommand)
    names = [f.name for f in flags]
    assert "--visible" in names
    assert "--hidden-flag" not in names


def test_extract_flags_default_values():
    flags = _extract_flags(GreetCommand)
    flag_map = {f.name: f for f in flags}
    # store_true flags have no meaningful default to document
    assert flag_map["--formal"].default_value == ""
    assert flag_map["--formal"].is_flag
    assert flag_map["--enthusiasm"].default_value == "1"
    assert flag_map["--suffix"].default_value == ""


def test_extract_flags_uses_longest_option_string():
    flags = _extract_flags(FarewellCommand)
    assert flags[0].name == "--formal"


def test_extract_flags_no_arg_command():
    """Test that _extract_flags works with a command that has no constructor arg."""
    flags = _extract_flags(NoArgCommand)
    assert len(flags) == 1
    assert flags[0].name == "--flag"
    assert flags[0].default_value == "val"
