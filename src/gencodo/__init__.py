"""gencodo -- Generate CLI reference documentation from argparse-based applications."""

from gencodo._core import gen_docs, gen_docs_tree, get_bundled_templates
from gencodo._types import (
    Command,
    CommandClass,
    CommandGroup,
    ExampleInfo,
    FlagInfo,
    TemplateInfo,
)

__all__ = [
    "Command",
    "CommandClass",
    "CommandGroup",
    "ExampleInfo",
    "FlagInfo",
    "TemplateInfo",
    "gen_docs",
    "gen_docs_tree",
    "get_bundled_templates",
]

__version__ = "0.2.0"
