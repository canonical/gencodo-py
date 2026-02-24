"""Type definitions for gencodo: protocols, dataclasses, and named tuples."""

from __future__ import annotations

import argparse
import dataclasses
from collections.abc import Sequence
from typing import NamedTuple, Protocol, runtime_checkable

__all__ = [
    "Command",
    "CommandGroup",
    "ExampleInfo",
    "FlagInfo",
    "TemplateInfo",
]


@runtime_checkable
class Command(Protocol):
    """Protocol that any CLI command class must satisfy.

    Any class with these attributes and methods can be used with gencodo
    via structural subtyping -- no inheritance required.
    """

    name: str
    """The command name as invoked on the command line."""
    help_msg: str
    """Short one-line help string."""
    overview: str
    """Longer description of the command (may be multi-line)."""
    hidden: bool
    """Whether this command should be excluded from generated documentation."""
    examples: list[tuple[str, str]]
    """List of (description, command_string) example pairs."""
    related_commands: list[str] | None
    """Explicit list of related command names, or None to infer from siblings."""

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser."""
        ...


class CommandGroup(NamedTuple):
    """A named group of commands."""

    name: str
    """Human-readable group name."""
    commands: Sequence[type[Command]]
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
