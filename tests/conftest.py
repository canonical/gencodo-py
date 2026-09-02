# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Shared fixtures with helper command classes satisfying the Command Protocol."""

from __future__ import annotations

import argparse

import pytest

from gencodo import CommandGroup


class GreetCommand:
    """A command with flags, examples, and related commands."""

    name = "greet"
    help_msg = "Greet a specific person"
    overview = (
        "The greet command allows you to personalize your greeting by specifying\n"
        "a name. You can also customize the greeting style and add an optional\n"
        "message suffix.\n\n"
        "This command demonstrates how to use positional and optional arguments\n"
        "with craft_cli."
    )
    hidden = False
    examples = [
        ("Greet Alice", "democli greet Alice"),
        ("Greet Bob formally", "democli greet Bob --formal"),
        ("Greet Charlie with enthusiasm", "democli greet Charlie --enthusiasm 5"),
        ("Greet multiple people", "democli greet Alice --suffix ', have a great day!'"),
    ]
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("name", help="Name of the person to greet")
        parser.add_argument(
            "--formal",
            action="store_true",
            default=False,
            help="Use formal greeting style",
        )
        parser.add_argument(
            "--enthusiasm",
            type=int,
            default=1,
            help="Enthusiasm level (1-5)",
        )
        parser.add_argument("--suffix", default=None, help="Optional message suffix")


class HelloCommand:
    """A simple command with no flags."""

    name = "hello"
    help_msg = "Say hello to the world"
    overview = "Prints a friendly hello message."
    hidden = False
    examples = [("Say hello", "democli hello")]
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass


class FarewellCommand:
    """Another simple command."""

    name = "farewell"
    help_msg = "Say goodbye"
    overview = "Prints a farewell message."
    hidden = False
    examples: list[tuple[str, str]] = []
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--formal", action="store_true", default=False, help="Use formal style"
        )


class HiddenCommand:
    """A hidden command that should be excluded from docs."""

    name = "secret"
    help_msg = "Secret command"
    overview = "This should not appear in documentation."
    hidden = True
    examples: list[tuple[str, str]] = []
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass


class SuppressedFlagCommand:
    """A command with a suppressed flag."""

    name = "suppress-test"
    help_msg = "Test suppressed flags"
    overview = "Has one visible and one suppressed flag."
    hidden = False
    examples: list[tuple[str, str]] = []
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--visible", help="Visible flag")
        parser.add_argument("--hidden-flag", help=argparse.SUPPRESS)


class NoArgCommand:
    """A command with a simple constructor (optional config)."""

    name = "simple"
    help_msg = "A simple command"
    overview = "No constructor args needed."
    hidden = False
    examples: list[tuple[str, str]] = []
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--flag", help="A flag", default="val")


class ExplicitRelatedCommand:
    """A command with explicit related_commands."""

    name = "explicit-related"
    help_msg = "Has explicit related commands"
    overview = "Tests explicit related_commands."
    hidden = False
    examples: list[tuple[str, str]] = []
    related_commands = ["greet", "hello"]

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass


@pytest.fixture
def command_groups() -> list[CommandGroup]:
    """Standard command groups for testing."""
    return [
        CommandGroup(
            name="Greetings",
            commands=[GreetCommand, HelloCommand, FarewellCommand],
        ),
        CommandGroup(
            name="Other",
            commands=[HiddenCommand, SuppressedFlagCommand],
        ),
    ]


@pytest.fixture
def all_groups_with_explicit() -> list[CommandGroup]:
    """Command groups including ExplicitRelatedCommand."""
    return [
        CommandGroup(
            name="Greetings",
            commands=[GreetCommand, HelloCommand, FarewellCommand],
        ),
        CommandGroup(
            name="Other",
            commands=[ExplicitRelatedCommand, HiddenCommand],
        ),
    ]
