# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Demonstrate gencodo usage with the demo CLI app.

Run from the project root:
    python examples/demo_cli/generate_docs.py
"""

from __future__ import annotations

import pathlib
import sys

from gencodo import CommandGroup, gen_docs_tree, get_bundled_templates

# Import the demo app's command definitions
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from app import COMMAND_GROUPS

# Tests override the destination by injecting OUTPUT_DIR_OVERRIDE into the globals.
OUTPUT_DIR = pathlib.Path(
    globals().get("OUTPUT_DIR_OVERRIDE") or pathlib.Path(__file__).parent / "docs_output"
)


def main() -> None:
    """Generate documentation for the demo CLI app."""
    # Convert the app's group tuples to gencodo CommandGroup namedtuples
    groups = [CommandGroup(name=name, commands=cmds) for name, cmds in COMMAND_GROUPS]

    # Generate reST documentation
    rst_templates = get_bundled_templates("rst")
    rst_dir = OUTPUT_DIR / "rst"
    generated_rst = gen_docs_tree(
        appname="democli",
        command_groups=groups,
        output_dir=rst_dir,
        templates=rst_templates,
        file_extension=".rst",
    )
    print(f"Generated reST docs in {rst_dir}/:")
    for f in generated_rst:
        print(f"  {f}")

    # Generate Markdown documentation
    md_templates = get_bundled_templates("md")
    md_dir = OUTPUT_DIR / "md"
    generated_md = gen_docs_tree(
        appname="democli",
        command_groups=groups,
        output_dir=md_dir,
        templates=md_templates,
    )
    print(f"\nGenerated Markdown docs in {md_dir}/:")
    for f in generated_md:
        print(f"  {f}")


if __name__ == "__main__":
    main()
