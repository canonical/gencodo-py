# Copyright 2021-2022 Canonical Ltd.
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

"""Documentation generation utilities for craft-cli applications."""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import re
from collections.abc import Callable
from typing import TextIO

from jinja2 import Environment, StrictUndefined
from jinja2.filters import do_indent

from craft_cli.dispatcher import BaseCommand, CommandGroup

__all__ = ["ExampleInfo", "FlagInfo", "TemplateInfo", "gen_docs", "gen_docs_tree"]


@dataclasses.dataclass(frozen=True, slots=True, eq=True, order=False)
class ExampleInfo:
    """Structured representation of a usage example."""

    info: str
    """Human-readable description of what the example demonstrates."""

    usage: str
    """The literal command string for the example."""


@dataclasses.dataclass(frozen=True, slots=True, eq=True, order=False)
class FlagInfo:
    """Structured representation of a single CLI flag."""

    name: str
    """The flag name as it appears on the command line (e.g., '--verbose')."""

    usage: str
    """One-line description of the flag's purpose."""

    default_value: str
    """The default value shown in documentation."""


@dataclasses.dataclass(frozen=True, slots=True, eq=True, order=False)
class TemplateInfo:
    """Jinja2 template configuration for documentation generation."""

    index_file_name: str
    """Output filename for the index document."""

    index_template: str
    """Jinja2 template string for the index document."""

    command_template: str
    """Jinja2 template string for per-command documents."""

    def __post_init__(self) -> None:
        """Validate that no field is empty or whitespace-only."""
        for field_name in ("index_file_name", "index_template", "command_template"):
            value = getattr(self, field_name)
            if not value.strip():
                raise ValueError(f"TemplateInfo.{field_name} must not be empty")


def _extract_flags(command_class: type[BaseCommand]) -> list[FlagInfo]:
    """Extract optional flags from a command class as FlagInfo objects.

    Creates an ArgumentParser with add_help=False, invokes fill_parser, then
    iterates over the parser's actions to collect optional flags (those with
    option_strings). Positional arguments and suppressed flags are excluded.
    """
    parser = argparse.ArgumentParser(prog=command_class.name, add_help=False)
    command_class(None).fill_parser(parser)
    flags: list[FlagInfo] = []
    for action in parser._actions:  # noqa: SLF001
        if not action.option_strings:
            continue  # skip positionals
        if action.help == argparse.SUPPRESS:
            continue  # skip suppressed
        name = max(action.option_strings, key=len)
        usage = action.help or ""
        if action.default is None or action.default is argparse.SUPPRESS:
            default = ""
        else:
            default = str(action.default)
        flags.append(FlagInfo(name=name, usage=usage, default_value=default))
    return flags


def _make_jinja_env() -> Environment:
    """Create a configured Jinja2 Environment for documentation generation.

    Returns an Environment with:
    - StrictUndefined: missing template variables raise UndefinedError
    - autoescape=False: safe for plain-text/Markdown output
    - trim_blocks=True, lstrip_blocks=True: cleaner template formatting
    - keep_trailing_newline=True: preserves trailing newlines in output
    - indent filter: indents all lines including the first (unlike Jinja2 default)
    - repeat filter: repeats a string N times
    """
    env = Environment(
        autoescape=False,  # noqa: S701 - intentional for doc generation, not HTML
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    def _indent(s: str, width: int = 4, *, blank: bool = False) -> str:
        return do_indent(s, width=width, first=True, blank=blank)

    def _repeat(s: str, n: int) -> str:
        return s * n

    env.filters["indent"] = _indent
    env.filters["repeat"] = _repeat
    return env


def _infer_related(
    command_class: type[BaseCommand],
    command_groups: list[CommandGroup],
) -> list[str]:
    """Determine the list of related command names for a command.

    If ``command_class.related_commands`` is not None, validate that all
    referenced names exist in the provided command_groups and return them
    as-is.  If any name is missing, raise ValueError.

    If ``command_class.related_commands`` is None, infer related commands from
    non-hidden siblings in the same CommandGroup, sorted alphabetically.

    Returns an empty list when the command is not found in any group or has no
    visible siblings.
    """
    if command_class.related_commands is not None:
        all_names = {c.name for g in command_groups for c in g.commands}
        for name in command_class.related_commands:
            if name not in all_names:
                raise ValueError(
                    f"related command {name!r} not found in command_groups"
                )
        return list(command_class.related_commands)
    # Infer from same group
    for group in command_groups:
        if command_class in group.commands:
            siblings = [
                c.name
                for c in group.commands
                if c is not command_class and not c.hidden
            ]
            return sorted(siblings)
    return []


def _build_template_context(
    command_class: type[BaseCommand],
    appname: str,
    command_groups: list[CommandGroup],
) -> dict[str, object]:
    """Build the complete Jinja2 template context dict for a command.

    Returns a dict with 10 keys: ref, command_name, short, long, synopsis,
    examples, flags, related_commands, heading_len, appname.

    Raises ValueError when command_name or help_msg is empty.
    """
    command_name = command_class.name
    short = command_class.help_msg
    if not command_name:
        raise ValueError("command_name must not be empty")
    if not short:
        raise ValueError("short (help_msg) must not be empty")

    long = (command_class.overview or "").strip()

    # synopsis from argparse format_usage()
    parser = argparse.ArgumentParser(prog=f"{appname} {command_name}", add_help=False)
    command_class(None).fill_parser(parser)
    raw_usage = parser.format_usage()
    synopsis = re.sub(r"^usage:\s*", "", raw_usage).strip()

    # Convert examples tuples to ExampleInfo
    examples = [
        ExampleInfo(info=info, usage=usage) for info, usage in command_class.examples
    ]

    flags = _extract_flags(command_class)
    related_commands = _infer_related(command_class, command_groups)
    heading_len = len(command_name)
    ref = command_name.replace("-", "_").replace(" ", "_")

    return {
        "ref": ref,
        "command_name": command_name,
        "short": short,
        "long": long,
        "synopsis": synopsis,
        "examples": examples,
        "flags": flags,
        "related_commands": related_commands,
        "heading_len": heading_len,
        "appname": appname,
    }


def gen_docs(
    command_class: type[BaseCommand],
    writer: TextIO,
    template: str,
    appname: str,
    command_groups: list[CommandGroup],
) -> None:
    """Render documentation for a single command to a writer.

    Compiles the provided Jinja2 template string, builds the template context
    for the given command, and writes the rendered output to *writer*.

    The writer is NOT flushed — the caller controls flushing.
    """
    env = _make_jinja_env()
    compiled = env.from_string(template)
    context = _build_template_context(command_class, appname, command_groups)
    writer.write(compiled.render(context))


def gen_docs_tree(
    appname: str,
    command_groups: list[CommandGroup],
    output_dir: pathlib.Path,
    templates: TemplateInfo,
    file_prepender: Callable[[str], str] | None = None,
    file_extension: str = ".md",
) -> list[str]:
    """Generate a documentation tree for all non-hidden commands.

    Writes one file per non-hidden command plus one index file into *output_dir*.
    Creates the directory if it does not exist. The *file_prepender* callback, if
    provided, is called with each filename and its return value is prepended to
    the file content.

    Returns a list of generated command filenames (the index file is excluded).
    """
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    env = _make_jinja_env()
    compiled_cmd = env.from_string(templates.command_template)
    compiled_idx = env.from_string(templates.index_template)

    generated: list[str] = []
    files_context: list[dict[str, str]] = []

    for group in command_groups:
        for cmd in group.commands:
            if cmd.hidden:
                continue
            filename = cmd.name.replace(" ", "-") + file_extension
            context = _build_template_context(cmd, appname, command_groups)
            content = compiled_cmd.render(context)
            if file_prepender is not None:
                content = file_prepender(filename) + content
            (output_dir / filename).write_text(content, encoding="utf-8")
            generated.append(filename)
            files_context.append({
                "filename": filename,
                "command_name": cmd.name,
                "short": cmd.help_msg,
                "group_name": group.name,
            })

    # Write index file
    idx_content = compiled_idx.render(files=files_context, appname=appname)
    if file_prepender is not None:
        idx_content = file_prepender(templates.index_file_name) + idx_content
    (output_dir / templates.index_file_name).write_text(idx_content, encoding="utf-8")

    return generated
