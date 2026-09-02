# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""gencodo -- Generate CLI reference documentation from argparse-based applications."""

from gencodo._core import gen_docs, gen_docs_tree, get_bundled_templates, validate_templates
from gencodo._jinja_env import BUILTIN_FILTERS
from gencodo._types import (
    ArgumentInfo,
    Command,
    CommandClass,
    CommandGroup,
    ExampleInfo,
    FlagInfo,
    TemplateInfo,
)

__all__ = [
    "BUILTIN_FILTERS",
    "ArgumentInfo",
    "Command",
    "CommandClass",
    "CommandGroup",
    "ExampleInfo",
    "FlagInfo",
    "TemplateInfo",
    "__version__",
    "gen_docs",
    "gen_docs_tree",
    "get_bundled_templates",
    "validate_templates",
]

__version__ = "0.4.0"
"""The single source of the package version (read by hatchling at build time)."""
