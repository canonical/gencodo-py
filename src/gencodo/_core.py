"""Core documentation generation logic for gencodo."""

from __future__ import annotations

import argparse
import importlib.resources
import pathlib
import re
from collections.abc import Callable, Sequence
from typing import Any, Literal, TextIO

from gencodo._jinja_env import _make_jinja_env
from gencodo._types import (
    Command,
    CommandGroup,
    ExampleInfo,
    FlagInfo,
    TemplateInfo,
)

__all__ = [
    "gen_docs",
    "gen_docs_tree",
    "get_bundled_templates",
]


def _instantiate_command(
    command_class: type[Command],
    command_config: Any = None,
) -> Command:
    """Instantiate a command class for parser introspection.

    If *command_config* is not None it is passed directly as the sole
    constructor argument.  Otherwise the legacy behaviour is preserved:
    tries command_class(None) first (craft_cli compatible), then
    command_class() for simple classes.
    """
    if command_config is not None:
        return command_class(command_config)  # type: ignore[call-arg]
    try:
        return command_class(None)  # type: ignore[call-arg]
    except TypeError:
        return command_class()  # type: ignore[call-arg]


def _extract_flags(
    command_class: type[Command],
    command_config: Any = None,
) -> list[FlagInfo]:
    """Extract optional flags from a command class as FlagInfo objects.

    Positional arguments and suppressed flags are excluded.
    The longest option string is used as the flag name.

    Args:
        command_class: A command class satisfying the Command protocol.
        command_config: Optional configuration object passed to the command constructor.

    Returns:
        A list of FlagInfo objects for the command's optional flags.
    """
    parser = argparse.ArgumentParser(prog=command_class.name, add_help=False)
    _instantiate_command(command_class, command_config).fill_parser(parser)
    flags: list[FlagInfo] = []
    for action in parser._actions:
        if not action.option_strings:
            continue
        if action.help == argparse.SUPPRESS:
            continue
        name = max(action.option_strings, key=len)
        usage = action.help or ""
        if action.default is None or action.default is argparse.SUPPRESS:
            default = ""
        else:
            default = str(action.default)
        flags.append(FlagInfo(name=name, usage=usage, default_value=default))
    return flags


def _infer_related(
    command_class: type[Command],
    command_groups: Sequence[CommandGroup],
) -> list[str]:
    """Determine the list of related command names for a command.

    If the command has explicit ``related_commands``, those are validated
    and returned. Otherwise, non-hidden siblings in the same group are returned.

    Args:
        command_class: The command class to find related commands for.
        command_groups: All command groups in the application.

    Returns:
        A list of related command names.

    Raises:
        ValueError: If an explicit related command name is not found.
    """
    if command_class.related_commands is not None:
        all_names = {c.name for g in command_groups for c in g.commands}
        for name in command_class.related_commands:
            if name not in all_names:
                raise ValueError(
                    f"related command {name!r} not found in command_groups"
                )
        return list(command_class.related_commands)
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
    command_class: type[Command],
    appname: str,
    command_groups: Sequence[CommandGroup],
    command_config: Any = None,
) -> dict[str, object]:
    """Build the complete Jinja2 template context dict for a command.

    Args:
        command_class: The command class to build context for.
        appname: The application name used in usage strings.
        command_groups: All command groups in the application.
        command_config: Optional configuration object passed to the command constructor.

    Returns:
        A dict with keys: ref, command_name, short, long, synopsis,
        examples, flags, related_commands, heading_len, appname.

    Raises:
        ValueError: If command_name or help_msg is empty.
    """
    command_name = command_class.name
    short = command_class.help_msg
    if not command_name:
        raise ValueError("command_name must not be empty")
    if not short:
        raise ValueError("short (help_msg) must not be empty")

    long = (command_class.overview or "").strip()

    parser = argparse.ArgumentParser(
        prog=f"{appname} {command_name}", add_help=False
    )
    _instantiate_command(command_class, command_config).fill_parser(parser)
    raw_usage = parser.format_usage()
    synopsis = re.sub(r"^usage:\s*", "", raw_usage).strip()

    examples = [
        ExampleInfo(info=info, usage=usage)
        for info, usage in command_class.examples
    ]

    flags = _extract_flags(command_class, command_config)
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
    command_class: type[Command],
    writer: TextIO,
    template: str,
    appname: str,
    command_groups: Sequence[CommandGroup],
    command_config: Any = None,
) -> None:
    """Render documentation for a single command to a writer.

    Args:
        command_class: The command class to document.
        writer: A text stream to write the rendered output to.
        template: A Jinja2 template string for the command page.
        appname: The application name used in usage strings.
        command_groups: All command groups (used for related commands).
        command_config: Optional configuration object passed to command constructors.
    """
    env = _make_jinja_env()
    compiled = env.from_string(template)
    context = _build_template_context(
        command_class, appname, command_groups, command_config
    )
    writer.write(compiled.render(context))


def gen_docs_tree(
    appname: str,
    command_groups: Sequence[CommandGroup],
    output_dir: pathlib.Path,
    templates: TemplateInfo,
    file_prepender: Callable[[str], str] | None = None,
    file_extension: str = ".md",
    command_config: Any = None,
) -> list[str]:
    """Generate a documentation tree for all non-hidden commands.

    Creates one file per command plus an index file in the output directory.

    Args:
        appname: The application name used in usage strings.
        command_groups: All command groups in the application.
        output_dir: Directory to write generated files into (created if needed).
        templates: Template configuration for index and command pages.
        file_prepender: Optional callable returning a string to prepend to each file.
        file_extension: File extension for command pages (default: ".md").
        command_config: Optional configuration object passed to command constructors.

    Returns:
        A list of generated command filenames (not including the index).
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
            context = _build_template_context(
                cmd, appname, command_groups, command_config
            )
            content = compiled_cmd.render(context)
            if file_prepender is not None:
                content = file_prepender(filename) + content
            (output_dir / filename).write_text(content, encoding="utf-8")
            generated.append(filename)
            files_context.append(
                {
                    "filename": filename,
                    "command_name": cmd.name,
                    "short": cmd.help_msg,
                    "group_name": group.name,
                }
            )

    idx_content = compiled_idx.render(files=files_context, appname=appname)
    if file_prepender is not None:
        idx_content = file_prepender(templates.index_file_name) + idx_content
    (output_dir / templates.index_file_name).write_text(
        idx_content, encoding="utf-8"
    )

    return generated


def get_bundled_templates(
    format: Literal["rst", "md"] = "rst",
    index_file_name: str | None = None,
) -> TemplateInfo:
    """Load bundled default templates for the given format.

    Args:
        format: Template format -- "rst" for reStructuredText, "md" for Markdown.
        index_file_name: Override the default index filename.
            Defaults to "index.rst" or "index.md" based on format.

    Returns:
        A TemplateInfo with the bundled templates loaded.

    Raises:
        ValueError: If format is not "rst" or "md".
    """
    if format not in ("rst", "md"):
        raise ValueError(f"format must be 'rst' or 'md', got {format!r}")

    templates_pkg = importlib.resources.files("gencodo") / "templates" / format
    command_template = (
        (templates_pkg / f"command.{format}.j2").read_text(encoding="utf-8")
    )
    index_template = (
        (templates_pkg / f"index.{format}.j2").read_text(encoding="utf-8")
    )

    if index_file_name is None:
        index_file_name = f"index.{format}"

    return TemplateInfo(
        index_file_name=index_file_name,
        index_template=index_template,
        command_template=command_template,
    )
