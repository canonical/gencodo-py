"""Type definitions for gencodo: protocols, dataclasses, and named tuples."""

from __future__ import annotations

import argparse
import dataclasses
from collections.abc import Sequence
from typing import Any, NamedTuple, Protocol, runtime_checkable

__all__ = [
    "Command",
    "CommandClass",
    "CommandGroup",
    "ExampleInfo",
    "FlagInfo",
    "TemplateInfo",
]


@runtime_checkable
class Command(Protocol):
    """Structural type for an instantiated command.

    Only attributes guaranteed by the base command interface belong here.
    Extension attributes (``overview``, ``examples``, ``related_commands``)
    are accessed via :func:`getattr` inside gencodo's rendering code.
    """

    name: str
    """The command name as invoked on the command line."""
    help_msg: str
    """Short one-line help string."""
    hidden: bool
    """Whether this command should be excluded from generated documentation."""

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser."""
        ...


@runtime_checkable
class CommandClass(Protocol):
    """Structural type for a command *class* (factory).

    Any class whose instances satisfy :class:`Command` and that exposes
    the required class-level attributes can be used with gencodo via
    structural subtyping -- no inheritance required.
    """

    name: str
    """The command name as invoked on the command line."""
    help_msg: str
    """Short one-line help string."""
    hidden: bool
    """Whether this command should be excluded from generated documentation."""

    def __call__(self, config: Any) -> Command:  # noqa: D102
        ...


class CommandGroup(NamedTuple):
    """A named group of commands."""

    name: str
    """Human-readable group name."""
    commands: Sequence[CommandClass]
    """Command classes in this group."""


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
