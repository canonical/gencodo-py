"""Tests for _infer_related."""

import pytest

from gencodo import CommandGroup
from gencodo._core import _infer_related
from tests.conftest import (
    ExplicitRelatedCommand,
    FarewellCommand,
    GreetCommand,
    HelloCommand,
    HiddenCommand,
)


def test_infer_related_from_siblings(command_groups):
    related = _infer_related(GreetCommand, command_groups)
    assert "hello" in related
    assert "farewell" in related
    assert "greet" not in related


def test_infer_related_sorted(command_groups):
    related = _infer_related(GreetCommand, command_groups)
    assert related == sorted(related)


def test_infer_related_excludes_hidden(command_groups):
    related = _infer_related(HiddenCommand, command_groups)
    # HiddenCommand is in "Other" group with SuppressedFlagCommand
    assert "secret" not in related


def test_infer_related_explicit(all_groups_with_explicit):
    related = _infer_related(ExplicitRelatedCommand, all_groups_with_explicit)
    assert related == ["greet", "hello"]


def test_infer_related_explicit_invalid():
    groups = [
        CommandGroup(name="Test", commands=[GreetCommand, HelloCommand]),
    ]
    # Create a command class with an invalid related command
    class BadRelated:
        name = "bad"
        help_msg = "Bad"
        overview = ""
        hidden = False
        examples = []
        related_commands = ["nonexistent"]

        def fill_parser(self, parser):
            pass

    with pytest.raises(ValueError, match="related command 'nonexistent' not found"):
        _infer_related(BadRelated, groups)


def test_infer_related_not_in_any_group():
    groups = [
        CommandGroup(name="Test", commands=[GreetCommand]),
    ]
    related = _infer_related(HelloCommand, groups)
    assert related == []
