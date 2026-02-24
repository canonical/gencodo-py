"""Example CLI app using plain argparse classes (no framework dependency).

Each command class satisfies the gencodo.Command protocol via duck typing.
"""

from __future__ import annotations

import argparse


class HelloCommand:
    """Say hello to the world."""

    name = "hello"
    help_msg = "Say hello to the world"
    overview = (
        "Prints a friendly hello message to standard output.\n\n"
        "This is the simplest possible command with no arguments."
    )
    hidden = False
    examples = [
        ("Say hello", "democli hello"),
    ]
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass


class GreetCommand:
    """Greet a specific person."""

    name = "greet"
    help_msg = "Greet a specific person"
    overview = (
        "The greet command allows you to personalize your greeting by specifying\n"
        "a name. You can also customize the greeting style and add an optional\n"
        "message suffix.\n\n"
        "This command demonstrates how to use positional and optional arguments."
    )
    hidden = False
    examples = [
        ("Greet Alice", "democli greet Alice"),
        ("Greet Bob formally", "democli greet Bob --formal"),
        ("Greet Charlie with enthusiasm", "democli greet Charlie --enthusiasm 5"),
        ("Greet with a suffix", "democli greet Alice --suffix ', have a great day!'"),
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
        parser.add_argument(
            "--suffix",
            default=None,
            help="Optional message suffix",
        )


class FarewellCommand:
    """Say goodbye."""

    name = "farewell"
    help_msg = "Say goodbye"
    overview = "Prints a farewell message. Supports formal and informal styles."
    hidden = False
    examples = [
        ("Say farewell", "democli farewell"),
        ("Formal farewell", "democli farewell --formal"),
    ]
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--formal",
            action="store_true",
            default=False,
            help="Use formal farewell style",
        )


# Command groups for use with gencodo
COMMAND_GROUPS = [
    ("Greetings", [HelloCommand, GreetCommand, FarewellCommand]),
]
