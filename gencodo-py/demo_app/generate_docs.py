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

"""Generate reStructuredText documentation for the demo CLI application.

This script demonstrates how to use craft_cli's gendocs module to automatically
generate CLI reference documentation in reStructuredText format suitable for
Sphinx documentation systems.

Usage:
    python generate_docs.py [output_directory]

If no output directory is specified, defaults to './docs_generated'.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import craft_cli
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import only what we need from craft_cli (avoiding full module initialization)
from craft_cli.dispatcher import BaseCommand, CommandGroup
from craft_cli.gendocs import TemplateInfo, gen_docs_tree


# Define commands inline to avoid importing the full demo_cli with dependencies
class HelloCommand(BaseCommand):
    name = "hello"
    help_msg = "Print a friendly greeting"
    overview = """The hello command prints a friendly greeting message to the terminal.

This is a simple command that demonstrates basic craft_cli functionality
without requiring any arguments. It's perfect for testing that your
installation is working correctly."""
    common = True
    examples = [
        ("Say hello with default message", "democli hello"),
        ("Use verbose mode to see debug info", "democli -v hello"),
    ]
    related_commands = ["greet"]

    def fill_parser(self, parser):
        pass

    def run(self, parsed_args):
        return 0


class GreetCommand(BaseCommand):
    name = "greet"
    help_msg = "Greet a specific person"
    overview = """The greet command allows you to personalize your greeting by specifying
a name. You can also customize the greeting style and add an optional
message suffix.

This command demonstrates how to use positional and optional arguments
with craft_cli."""
    common = True
    examples = [
        ("Greet Alice", "democli greet Alice"),
        ("Greet Bob formally", "democli greet Bob --formal"),
        ("Greet Charlie with enthusiasm", "democli greet Charlie --enthusiasm 5"),
        ("Greet multiple people", "democli greet Alice --suffix ', have a great day!'"),
    ]
    related_commands = ["hello", "farewell"]

    def fill_parser(self, parser):
        parser.add_argument("name", help="Name of the person to greet")
        parser.add_argument(
            "--formal", action="store_true", help="Use formal greeting style"
        )
        parser.add_argument(
            "--enthusiasm", type=int, default=1, help="Enthusiasm level (1-5)"
        )
        parser.add_argument("--suffix", default="", help="Optional message suffix")

    def run(self, parsed_args):
        return 0


class FarewellCommand(BaseCommand):
    name = "farewell"
    help_msg = "Say goodbye to someone"
    overview = """The farewell command provides a way to say goodbye in various styles.

Choose from casual, formal, or sad farewell styles. You can optionally
include a wish for the future or mention when you'll meet again."""
    examples = [
        ("Simple goodbye", "democli farewell"),
        ("Formal farewell to Bob", "democli farewell --name Bob --style formal"),
        ("Sad goodbye", "democli farewell --style sad"),
        ("Goodbye with future wish", "democli farewell --wish 'see you soon'"),
    ]
    related_commands = ["greet"]

    def fill_parser(self, parser):
        parser.add_argument("--name", help="Name of the person (optional)")
        parser.add_argument(
            "--style",
            choices=["casual", "formal", "sad"],
            default="casual",
            help="Farewell style",
        )
        parser.add_argument("--wish", help="Add a wish for the future")

    def run(self, parsed_args):
        return 0


class ListItemsCommand(BaseCommand):
    name = "list-items"
    help_msg = "Display a list of items"
    overview = """The list-items command shows a configurable list of items with various
filtering and display options.

You can filter by category, search by keyword, limit the number of results,
and choose between different output formats."""
    examples = [
        ("List all items", "democli list-items"),
        ("List items in fruit category", "democli list-items --category fruit"),
        ("Search for items containing 'apple'", "democli list-items --search apple"),
        ("Show only 5 items", "democli list-items --limit 5"),
        ("Show detailed output", "democli list-items --format detailed"),
    ]
    related_commands = None  # Will infer from same group

    def fill_parser(self, parser):
        parser.add_argument("--category", help="Filter by category")
        parser.add_argument("--search", help="Search keyword in item names")
        parser.add_argument(
            "--limit", type=int, default=10, help="Maximum number of items to show"
        )
        parser.add_argument(
            "--format",
            choices=["simple", "detailed", "json"],
            default="simple",
            help="Output format",
        )

    def run(self, parsed_args):
        return 0


class DebugCommand(BaseCommand):
    name = "debug"
    help_msg = "Internal debug command"
    overview = "This command is hidden and used for internal debugging only."
    hidden = True

    def fill_parser(self, parser):
        pass

    def run(self, parsed_args):
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


def load_template(template_path: Path) -> str:
    """Load a template file and return its contents as a string."""
    return template_path.read_text(encoding="utf-8")


def main() -> int:
    """Generate CLI reference documentation."""
    parser = argparse.ArgumentParser(
        description="Generate reStructuredText CLI reference documentation"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="docs_generated",
        help="Output directory for generated documentation (default: docs_generated)",
    )
    parser.add_argument(
        "--appname",
        default="democli",
        help="Application name to use in documentation (default: democli)",
    )
    args = parser.parse_args()

    # Define paths
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    output_dir = Path(args.output_dir)

    # Load templates
    print(f"📖 Loading templates from {template_dir}")
    command_template = load_template(template_dir / "command_template.rst")
    index_template = load_template(template_dir / "index_template.rst")

    # Create TemplateInfo
    templates = TemplateInfo(
        index_file_name="index.rst",
        index_template=index_template,
        command_template=command_template,
    )

    # Generate documentation
    print(f"📝 Generating documentation for {args.appname}...")
    print(f"📂 Output directory: {output_dir.absolute()}")

    generated_files = gen_docs_tree(
        appname=args.appname,
        command_groups=COMMAND_GROUPS,
        output_dir=output_dir,
        templates=templates,
        file_extension=".rst",
    )

    # Report results
    print(f"\n✅ Successfully generated {len(generated_files)} command documents:")
    for filename in sorted(generated_files):
        print(f"   • {filename}")

    print("\n📑 Index file: index.rst")
    print("\n🎉 Documentation generation complete!")
    print("\nTo view the generated documentation:")
    print(f"   1. Navigate to: {output_dir.absolute()}")
    print("   2. Open any .rst file in a text editor")
    print("\nTo build with Sphinx:")
    print("   1. Copy the generated files to your Sphinx source directory")
    print("   2. Include index.rst in your documentation toctree")
    print("   3. Run: sphinx-build -b html <source_dir> <build_dir>")

    return 0


if __name__ == "__main__":
    sys.exit(main())
