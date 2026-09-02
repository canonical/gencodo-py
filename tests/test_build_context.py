# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for _build_template_context."""

import pytest

from gencodo._core import _build_template_context
from gencodo._types import ExampleInfo, FlagInfo
from tests.conftest import GreetCommand, HelloCommand


def test_context_keys(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    expected_keys = {
        "ref",
        "command_name",
        "short",
        "long",
        "synopsis",
        "examples",
        "arguments",
        "flags",
        "related_commands",
        "heading_len",
        "appname",
        "hidden",
        "common",
        "group_name",
        "filename",
    }
    assert set(ctx.keys()) == expected_keys


def test_context_ref(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    assert ctx["ref"] == "greet"


def test_context_command_name(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    assert ctx["command_name"] == "greet"


def test_context_short(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    assert ctx["short"] == "Greet a specific person"


def test_context_long(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    assert "personalize your greeting" in ctx["long"]


def test_context_synopsis(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    assert "democli greet" in ctx["synopsis"]


def test_context_examples(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    examples = ctx["examples"]
    assert len(examples) == 4
    assert all(isinstance(e, ExampleInfo) for e in examples)
    assert examples[0].info == "Greet Alice"


def test_context_flags(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    flags = ctx["flags"]
    assert all(isinstance(f, FlagInfo) for f in flags)
    flag_names = [f.name for f in flags]
    assert "--formal" in flag_names


def test_context_related_commands(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    assert "hello" in ctx["related_commands"]
    assert "farewell" in ctx["related_commands"]


def test_context_heading_len(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    assert ctx["heading_len"] == len("greet")


def test_context_appname(command_groups):
    ctx = _build_template_context(GreetCommand, "democli", command_groups)
    assert ctx["appname"] == "democli"


def test_context_ref_hyphenated(command_groups):
    """ref replaces hyphens and spaces with underscores."""

    class HyphenCommand:
        name = "my-command"
        help_msg = "A hyphenated command"
        overview = ""
        hidden = False
        examples = []
        related_commands = None

        def __init__(self, config=None):
            pass

        def fill_parser(self, parser):
            pass

    groups = [type(command_groups[0])("Test", [HyphenCommand])]
    ctx = _build_template_context(HyphenCommand, "app", groups)
    assert ctx["ref"] == "my_command"


def test_context_empty_name_raises(command_groups):
    class EmptyName:
        name = ""
        help_msg = "Help"
        overview = ""
        hidden = False
        examples = []
        related_commands = None

        def __init__(self, config=None):
            pass

        def fill_parser(self, parser):
            pass

    with pytest.raises(ValueError, match="command_name must not be empty"):
        _build_template_context(EmptyName, "app", command_groups)


def test_context_empty_help_raises(command_groups):
    class EmptyHelp:
        name = "test"
        help_msg = ""
        overview = ""
        hidden = False
        examples = []
        related_commands = None

        def __init__(self, config=None):
            pass

        def fill_parser(self, parser):
            pass

    with pytest.raises(ValueError, match="short .* must not be empty"):
        _build_template_context(EmptyHelp, "app", command_groups)


def test_context_long_stripped(command_groups):
    ctx = _build_template_context(HelloCommand, "democli", command_groups)
    long = ctx["long"]
    assert long == long.strip()
