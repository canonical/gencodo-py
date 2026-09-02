# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Core documentation generation logic for gencodo."""

from __future__ import annotations

import argparse
import importlib.resources
import pathlib
from collections.abc import Callable, Sequence
from typing import Any, Literal, TextIO

from gencodo._jinja_env import Filters, _make_jinja_env
from gencodo._types import (
    ArgumentInfo,
    CommandClass,
    CommandGroup,
    ExampleInfo,
    FlagInfo,
    TemplateInfo,
)

__all__ = [
    "gen_docs",
    "gen_docs_tree",
    "get_bundled_templates",
    "validate_templates",
]

_USAGE_WIDTH = 10**6
"""Formatter width that keeps ``format_usage()`` on a single line."""


def _instantiate_command(
    command_class: CommandClass,
    command_config: Any = None,  # noqa: ANN401 - opaque, passed through
) -> Any:  # noqa: ANN401 - see Command docstring
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
        return command_class()


def _build_parser(
    command_class: CommandClass,
    prog: str,
    command_config: Any = None,  # noqa: ANN401
) -> argparse.ArgumentParser:
    """Create a parser for *command_class* and let the command fill it."""
    parser = argparse.ArgumentParser(
        prog=prog,
        add_help=False,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, width=_USAGE_WIDTH),
    )
    _instantiate_command(command_class, command_config).fill_parser(parser)
    return parser


def _format_default(action: argparse.Action) -> str:
    if action.default is None or action.default is argparse.SUPPRESS:
        return ""
    return str(action.default)


def _format_choices(action: argparse.Action) -> tuple[str, ...]:
    if not action.choices:
        return ()
    return tuple(str(choice) for choice in action.choices)


def _extract_arguments(
    parser: argparse.ArgumentParser,
) -> tuple[list[ArgumentInfo], list[FlagInfo]]:
    """Split a parser's actions into positional arguments and optional flags.

    Suppressed actions (``help=argparse.SUPPRESS``) are excluded from both.

    Returns:
        A ``(arguments, flags)`` pair in parser declaration order.
    """
    arguments: list[ArgumentInfo] = []
    flags: list[FlagInfo] = []
    for action in parser._actions:  # noqa: SLF001 - argparse has no public accessor
        if action.help == argparse.SUPPRESS:
            continue
        usage = action.help or ""
        metavar = "" if action.metavar is None else str(action.metavar)
        choices = _format_choices(action)
        if not action.option_strings:
            arguments.append(
                ArgumentInfo(
                    name=metavar or action.dest,
                    usage=usage,
                    metavar=metavar,
                    nargs="" if action.nargs is None else str(action.nargs),
                    choices=choices,
                    default_value=_format_default(action),
                )
            )
            continue
        is_flag = action.nargs == 0
        name = max(action.option_strings, key=len)
        short = min(action.option_strings, key=len)
        flags.append(
            FlagInfo(
                name=name,
                usage=usage,
                default_value="" if is_flag else _format_default(action),
                short=short if short != name else "",
                option_strings=tuple(action.option_strings),
                metavar="" if is_flag else metavar,
                choices=choices,
                required=bool(action.required),
                is_flag=is_flag,
            )
        )
    return arguments, flags


def _extract_flags(
    command_class: CommandClass,
    command_config: Any = None,  # noqa: ANN401
) -> list[FlagInfo]:
    """Extract optional flags from a command class as FlagInfo objects.

    Positional arguments and suppressed flags are excluded; see
    :func:`_extract_arguments` for both lists at once.
    """
    parser = _build_parser(command_class, command_class.name, command_config)
    return _extract_arguments(parser)[1]


def _infer_related(
    command_class: CommandClass,
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
    explicit: list[str] | None = getattr(command_class, "related_commands", None)
    if explicit is not None:
        all_names = {c.name for g in command_groups for c in g.commands}
        for name in explicit:
            if name not in all_names:
                msg = f"related command {name!r} not found in command_groups"
                raise ValueError(msg)
        return list(explicit)
    for group in command_groups:
        if command_class in group.commands:
            siblings = [c.name for c in group.commands if c is not command_class and not c.hidden]
            return sorted(siblings)
    return []


def _group_of(
    command_class: CommandClass,
    command_groups: Sequence[CommandGroup],
) -> str:
    for group in command_groups:
        if command_class in group.commands:
            return group.name
    return ""


def _file_name(command_class: CommandClass, file_prefix: str, file_extension: str) -> str:
    return file_prefix + command_class.name.replace(" ", "-") + file_extension


def _build_template_context(
    command_class: CommandClass,
    appname: str,
    command_groups: Sequence[CommandGroup],
    command_config: Any = None,  # noqa: ANN401
    *,
    file_prefix: str = "",
    file_extension: str = "",
) -> dict[str, Any]:
    """Build the complete Jinja2 template context dict for a command.

    Args:
        command_class: The command class to build context for.
        appname: The application name used in usage strings.
        command_groups: All command groups in the application.
        command_config: Optional configuration object passed to the command constructor.
        file_prefix: Prefix of the command's file name (as in :func:`gen_docs_tree`).
        file_extension: Extension of the command's file name.

    Returns:
        A dict with the keys documented in the README under
        "Command template variables".

    Raises:
        ValueError: If command_name or help_msg is empty.
    """
    command_name = command_class.name
    short = command_class.help_msg
    if not command_name:
        msg = "command_name must not be empty"
        raise ValueError(msg)
    if not short:
        msg = "short (help_msg) must not be empty"
        raise ValueError(msg)

    overview: str = getattr(command_class, "overview", "")
    long = (overview or "").strip()

    parser = _build_parser(command_class, f"{appname} {command_name}", command_config)
    synopsis = parser.format_usage().removeprefix("usage:").strip()
    arguments, flags = _extract_arguments(parser)

    raw_examples: list[tuple[str, str]] = getattr(command_class, "examples", [])
    examples = [ExampleInfo(info=info, usage=usage) for info, usage in raw_examples]

    related_commands = _infer_related(command_class, command_groups)
    ref = command_name.replace("-", "_").replace(" ", "_")

    return {
        "ref": ref,
        "command_name": command_name,
        "short": short,
        "long": long,
        "synopsis": synopsis,
        "examples": examples,
        "arguments": arguments,
        "flags": flags,
        "related_commands": related_commands,
        "heading_len": len(command_name),
        "appname": appname,
        "hidden": bool(getattr(command_class, "hidden", False)),
        "common": bool(getattr(command_class, "common", False)),
        "group_name": _group_of(command_class, command_groups),
        "filename": _file_name(command_class, file_prefix, file_extension),
    }


def gen_docs(
    command_class: CommandClass,
    writer: TextIO,
    template: str,
    appname: str,
    command_groups: Sequence[CommandGroup],
    command_config: Any = None,  # noqa: ANN401
    *,
    extra_filters: Filters | None = None,
) -> None:
    """Render documentation for a single command to a writer.

    Args:
        command_class: The command class to document.
        writer: A text stream to write the rendered output to.
        template: A Jinja2 template string for the command page.
        appname: The application name used in usage strings.
        command_groups: All command groups (used for related commands).
        command_config: Optional configuration object passed to command constructors.
        extra_filters: Additional Jinja2 filters available to the template.
    """
    env = _make_jinja_env(extra_filters)
    compiled = env.from_string(template)
    context = _build_template_context(command_class, appname, command_groups, command_config)
    writer.write(compiled.render(context))


def gen_docs_tree(
    appname: str,
    command_groups: Sequence[CommandGroup],
    output_dir: pathlib.Path,
    templates: TemplateInfo,
    file_prepender: Callable[[str], str] | None = None,
    file_extension: str = ".md",
    command_config: Any = None,  # noqa: ANN401
    *,
    file_prefix: str = "",
    extra_filters: Filters | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Generate a documentation tree for all non-hidden commands.

    Creates one file per command plus an index file in the output directory.
    Every page is rendered before anything is written, so a template error
    leaves no partial output behind.

    Args:
        appname: The application name used in usage strings.
        command_groups: All command groups in the application.
        output_dir: Directory to write generated files into (created if needed).
        templates: Template configuration for index and command pages.
        file_prepender: Optional callable returning a string to prepend to each file;
            it receives the file name.
        file_extension: File extension for command pages (default: ".md").
        command_config: Optional configuration object passed to command constructors.
        file_prefix: Prefix for command page file names, e.g. ``"myapp-"``.
        extra_filters: Additional Jinja2 filters available to both templates.
        dry_run: Render everything but write nothing.

    Returns:
        A list of generated command filenames (not including the index).
    """
    output_dir = pathlib.Path(output_dir)

    env = _make_jinja_env(extra_filters)
    compiled_cmd = env.from_string(templates.command_template)
    compiled_idx = env.from_string(templates.index_template)

    rendered: list[tuple[str, str]] = []
    files_context: list[dict[str, str]] = []

    for group in command_groups:
        for cmd in group.commands:
            if cmd.hidden:
                continue
            context = _build_template_context(
                cmd,
                appname,
                command_groups,
                command_config,
                file_prefix=file_prefix,
                file_extension=file_extension,
            )
            filename = str(context["filename"])
            content = compiled_cmd.render(context)
            if file_prepender is not None:
                content = file_prepender(filename) + content
            rendered.append((filename, content))
            files_context.append(
                {
                    "filename": filename,
                    "command_name": cmd.name,
                    "short": cmd.help_msg,
                    "group_name": group.name,
                    "ref": str(context["ref"]),
                }
            )

    idx_content = compiled_idx.render(files=files_context, commands=files_context, appname=appname)
    if file_prepender is not None:
        idx_content = file_prepender(templates.index_file_name) + idx_content
    rendered.append((templates.index_file_name, idx_content))

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in rendered:
            (output_dir / filename).write_text(content, encoding="utf-8")

    return [filename for filename, _ in rendered[:-1]]


def _synthetic_contexts(appname: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a fully populated and a minimal command context for validation."""
    full: dict[str, Any] = {
        "ref": "app_group_cmd",
        "command_name": "group-cmd",
        "short": "Do the thing",
        "long": "Do the thing, at length.\n\nSecond paragraph.",
        "synopsis": f"{appname} group-cmd [-f] [--name NAME] SDK [PARTS ...]",
        "examples": [
            ExampleInfo(info="Do it", usage=f"{appname} group-cmd my-sdk"),
            ExampleInfo(info="Force it", usage=f"{appname} group-cmd my-sdk --force"),
        ],
        "arguments": [
            ArgumentInfo(name="SDK", usage="Name of the SDK", metavar="SDK"),
            ArgumentInfo(name="PARTS", usage="Parts to build", metavar="PARTS", nargs="*"),
        ],
        "flags": [
            FlagInfo(
                name="--force",
                usage="Force it",
                default_value="",
                short="-f",
                option_strings=("-f", "--force"),
                is_flag=True,
            ),
            FlagInfo(
                name="--name",
                usage="Name to use",
                default_value="default",
                option_strings=("--name",),
                metavar="NAME",
                choices=("a", "b"),
                required=True,
            ),
        ],
        "related_commands": ["other", "third"],
        "heading_len": len("group-cmd"),
        "appname": appname,
        "hidden": False,
        "common": True,
        "group_name": "Group",
        "filename": "group-cmd.rst",
    }
    minimal: dict[str, Any] = {
        "ref": "leaf",
        "command_name": "leaf",
        "short": "Leaf",
        "long": "",
        "synopsis": f"{appname} leaf",
        "examples": [],
        "arguments": [],
        "flags": [],
        "related_commands": [],
        "heading_len": len("leaf"),
        "appname": appname,
        "hidden": False,
        "common": False,
        "group_name": "",
        "filename": "leaf.rst",
    }
    return full, minimal


def validate_templates(
    templates: TemplateInfo,
    *,
    appname: str = "app",
    extra_filters: Filters | None = None,
) -> None:
    """Check that templates compile and render, without any command classes.

    The command template is rendered against a fully populated synthetic
    context (every list non-empty, every string set) and against a minimal
    one (so that ``else`` branches run too); the index template is rendered
    against an index listing both. Unknown variables or filters raise, as
    they would during generation.

    Args:
        templates: Template configuration to validate.
        appname: Application name used in the synthetic contexts.
        extra_filters: The filters you pass to the generators, so custom
            filter names are known.

    Raises:
        jinja2.TemplateError: If a template fails to compile or render.
    """
    env = _make_jinja_env(extra_filters)
    compiled_cmd = env.from_string(templates.command_template)
    compiled_idx = env.from_string(templates.index_template)

    full, minimal = _synthetic_contexts(appname)
    files_context: list[dict[str, str]] = []
    for context in (full, minimal):
        compiled_cmd.render(context)
        files_context.append(
            {
                "filename": str(context["filename"]),
                "command_name": str(context["command_name"]),
                "short": str(context["short"]),
                "group_name": str(context["group_name"]),
                "ref": str(context["ref"]),
            }
        )
    compiled_idx.render(files=files_context, commands=files_context, appname=appname)


def get_bundled_templates(
    format: Literal["rst", "md"] = "rst",  # noqa: A002 - public API name
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
        msg = f"format must be 'rst' or 'md', got {format!r}"
        raise ValueError(msg)

    templates_pkg = importlib.resources.files("gencodo") / "templates" / format
    command_template = (templates_pkg / f"command.{format}.j2").read_text(encoding="utf-8")
    index_template = (templates_pkg / f"index.{format}.j2").read_text(encoding="utf-8")

    if index_file_name is None:
        index_file_name = f"index.{format}"

    return TemplateInfo(
        index_file_name=index_file_name,
        index_template=index_template,
        command_template=command_template,
    )
