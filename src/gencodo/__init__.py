"""gencodo -- Generate CLI reference documentation from argparse-based applications."""

from gencodo._core import gen_docs, gen_docs_tree, get_bundled_templates
from gencodo._types import (
    Command,
    CommandGroup,
    ExampleInfo,
    FlagInfo,
    TemplateInfo,
)

__all__ = [
    "Command",
    "CommandGroup",
    "ExampleInfo",
    "FlagInfo",
    "TemplateInfo",
    "gen_docs",
    "gen_docs_tree",
    "get_bundled_templates",
]

__version__ = "0.1.1"
