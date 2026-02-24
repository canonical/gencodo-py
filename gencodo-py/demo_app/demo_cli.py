#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Demo application showcasing craft_cli documentation generation capabilities."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import craft_cli
sys.path.insert(0, str(Path(__file__).parent.parent))

from craft_cli import emit
from craft_cli.dispatcher import BaseCommand, CommandGroup, Dispatcher


class HelloCommand(BaseCommand):
    """Say hello to the world."""

    name = "hello"
    help_msg = "Print a friendly greeting"
    overview = """
    The hello command prints a friendly greeting message to the terminal.

    This is a simple command that demonstrates basic craft_cli functionality
    without requiring any arguments. It's perfect for testing that your
    installation is working correctly.
    """
    common = True

    examples = [
        ("Say hello with default message", "democli hello"),
        ("Use verbose mode to see debug info", "democli -v hello"),
    ]

    related_commands = ["greet"]

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        """No arguments needed for hello command."""

    def run(self, parsed_args: argparse.Namespace) -> int | None:
        """Execute the hello command."""
        emit.message("Hello, World! 👋")
        emit.verbose("This is a verbose debug message")
        return 0


class GreetCommand(BaseCommand):
    """Greet someone by name."""

    name = "greet"
    help_msg = "Greet a specific person"
    overview = """
    The greet command allows you to personalize your greeting by specifying
    a name. You can also customize the greeting style and add an optional
    message suffix.

    This command demonstrates how to use positional and optional arguments
    with craft_cli.
    """
    common = True

    examples = [
        ("Greet Alice", "democli greet Alice"),
        ("Greet Bob formally", "democli greet Bob --formal"),
        ("Greet Charlie with enthusiasm", "democli greet Charlie --enthusiasm 5"),
        ("Greet multiple people", "democli greet Alice --suffix ', have a great day!'"),
    ]

    related_commands = ["hello", "farewell"]

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add greet command arguments."""
        parser.add_argument(
            "name",
            help="Name of the person to greet",
        )
        parser.add_argument(
            "--formal",
            action="store_true",
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
            default="",
            help="Optional message suffix",
        )

    def run(self, parsed_args: argparse.Namespace) -> int | None:
        """Execute the greet command."""
        if parsed_args.formal:
            greeting = f"Good day, {parsed_args.name}"
        else:
            greeting = f"Hey {parsed_args.name}"

        exclamation = "!" * min(parsed_args.enthusiasm, 5)
        message = f"{greeting}{exclamation}{parsed_args.suffix}"

        emit.message(message)
        return 0


class FarewellCommand(BaseCommand):
    """Say goodbye."""

    name = "farewell"
    help_msg = "Say goodbye to someone"
    overview = """
    The farewell command provides a way to say goodbye in various styles.

    Choose from casual, formal, or sad farewell styles. You can optionally
    include a wish for the future or mention when you'll meet again.
    """

    examples = [
        ("Simple goodbye", "democli farewell"),
        ("Formal farewell to Bob", "democli farewell --name Bob --style formal"),
        ("Sad goodbye", "democli farewell --style sad"),
        ("Goodbye with future wish", "democli farewell --wish 'see you soon'"),
    ]

    related_commands = ["greet"]

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add farewell command arguments."""
        parser.add_argument(
            "--name",
            help="Name of the person (optional)",
        )
        parser.add_argument(
            "--style",
            choices=["casual", "formal", "sad"],
            default="casual",
            help="Farewell style",
        )
        parser.add_argument(
            "--wish",
            help="Add a wish for the future",
        )

    def run(self, parsed_args: argparse.Namespace) -> int | None:
        """Execute the farewell command."""
        name_part = f" {parsed_args.name}" if parsed_args.name else ""

        if parsed_args.style == "formal":
            message = f"Farewell{name_part}, it was a pleasure."
        elif parsed_args.style == "sad":
            message = f"Goodbye{name_part}, I'll miss you..."
        else:
            message = f"See you later{name_part}!"

        if parsed_args.wish:
            message += f" {parsed_args.wish}"

        emit.message(message)
        return 0


class ListItemsCommand(BaseCommand):
    """List items with filtering options."""

    name = "list-items"
    help_msg = "Display a list of items"
    overview = """
    The list-items command shows a configurable list of items with various
    filtering and display options.

    You can filter by category, search by keyword, limit the number of results,
    and choose between different output formats.
    """

    examples = [
        ("List all items", "democli list-items"),
        ("List items in fruit category", "democli list-items --category fruit"),
        ("Search for items containing 'apple'", "democli list-items --search apple"),
        ("Show only 5 items", "democli list-items --limit 5"),
        ("Show detailed output", "democli list-items --format detailed"),
    ]

    related_commands = ["search", "filter"]

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add list-items command arguments."""
        parser.add_argument(
            "--category",
            help="Filter by category",
        )
        parser.add_argument(
            "--search",
            help="Search keyword in item names",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of items to show",
        )
        parser.add_argument(
            "--format",
            choices=["simple", "detailed", "json"],
            default="simple",
            help="Output format",
        )

    def run(self, parsed_args: argparse.Namespace) -> int | None:
        """Execute the list-items command."""
        items = [
            ("apple", "fruit"),
            ("banana", "fruit"),
            ("carrot", "vegetable"),
            ("date", "fruit"),
            ("eggplant", "vegetable"),
        ]

        # Apply filters
        filtered = items
        if parsed_args.category:
            filtered = [i for i in filtered if i[1] == parsed_args.category]
        if parsed_args.search:
            filtered = [
                i for i in filtered if parsed_args.search.lower() in i[0].lower()
            ]

        # Apply limit
        filtered = filtered[: parsed_args.limit]

        # Display
        emit.message(f"Found {len(filtered)} items:")
        for item_name, item_cat in filtered:
            if parsed_args.format == "detailed":
                emit.message(f"  • {item_name} (category: {item_cat})")
            elif parsed_args.format == "json":
                emit.message(f'  {{"name": "{item_name}", "category": "{item_cat}"}}')
            else:
                emit.message(f"  • {item_name}")

        return 0


# Hidden command (won't appear in docs)
class DebugCommand(BaseCommand):
    """Debug command for internal use."""

    name = "debug"
    help_msg = "Internal debug command"
    overview = "This command is hidden and used for internal debugging only."
    hidden = True

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        """No arguments needed."""

    def run(self, parsed_args: argparse.Namespace) -> int | None:
        """Execute debug command."""
        emit.message("Debug mode activated")
        return 0


# Define command groups
COMMAND_GROUPS = [
    CommandGroup(
        name="Basic Commands",
        commands=[HelloCommand, GreetCommand, FarewellCommand],
        ordered=False,
    ),
    CommandGroup(
        name="Data Commands",
        commands=[ListItemsCommand],
        ordered=False,
    ),
    CommandGroup(
        name="Hidden Commands",
        commands=[DebugCommand],
        ordered=False,
    ),
]


def main() -> int:
    """Run the demo CLI application."""
    # Initialize the emitter
    from craft_cli import CraftError, EmitterMode
    from craft_cli.errors import ArgumentParsingError, ProvideHelpException

    emit.init(EmitterMode.BRIEF, "democli", "Welcome to democli!")

    dispatcher = Dispatcher(
        appname="democli",
        commands_groups=COMMAND_GROUPS,
        summary="A demo CLI application showcasing craft_cli features",
    )

    try:
        dispatcher.pre_parse_args(sys.argv[1:])
        dispatcher.load_command(None)
        return_code = dispatcher.run()
        emit.ended_ok()
        return return_code or 0
    except ProvideHelpException as err:
        print(err)
        return 0
    except ArgumentParsingError as err:
        print(err, file=sys.stderr)
        return 1
    except CraftError as err:
        emit.error(err)
        return 1
    except KeyboardInterrupt:
        emit.message("Interrupted.")
        return 130
    except Exception as err:
        emit.error(err)
        return 1


if __name__ == "__main__":
    sys.exit(main())
