# Meta-Prompt: Bootstrap `gencodo-py` Python Package

## Purpose

Create a standalone, PyPI-publishable Python package called **gencodo-py** (import name: `gencodo`) that generates CLI reference documentation from argparse-based applications using Jinja2 templates. The package is inspired by an internal `craft_cli.gendocs` module but is completely standalone with zero framework dependencies beyond `jinja2`.

---

## Role

You are an expert Python package author. You will bootstrap the entire `gencodo-py` package from scratch: project scaffolding, source code, tests, packaging metadata, bundled templates, and a working example. Every file you produce must be complete and production-ready for PyPI publication.

---

## Reference Material

The design is derived from the following source files from an unpublished `craft_cli` module. Study them carefully to understand the architecture, then adapt it for a standalone package that works with **any** argparse-based CLI app via a Protocol interface (no inheritance required).

### Reference: `gendocs.py` (core module)

```python
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
    """Extract optional flags from a command class as FlagInfo objects."""
    parser = argparse.ArgumentParser(prog=command_class.name, add_help=False)
    command_class(None).fill_parser(parser)
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


def _make_jinja_env() -> Environment:
    """Create a configured Jinja2 Environment for documentation generation."""
    env = Environment(
        autoescape=False,
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
    """Determine the list of related command names for a command."""
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
    command_class: type[BaseCommand],
    appname: str,
    command_groups: list[CommandGroup],
) -> dict[str, object]:
    """Build the complete Jinja2 template context dict for a command."""
    command_name = command_class.name
    short = command_class.help_msg
    if not command_name:
        raise ValueError("command_name must not be empty")
    if not short:
        raise ValueError("short (help_msg) must not be empty")

    long = (command_class.overview or "").strip()

    parser = argparse.ArgumentParser(prog=f"{appname} {command_name}", add_help=False)
    command_class(None).fill_parser(parser)
    raw_usage = parser.format_usage()
    synopsis = re.sub(r"^usage:\s*", "", raw_usage).strip()

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
    """Render documentation for a single command to a writer."""
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
    """Generate a documentation tree for all non-hidden commands."""
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

    idx_content = compiled_idx.render(files=files_context, appname=appname)
    if file_prepender is not None:
        idx_content = file_prepender(templates.index_file_name) + idx_content
    (output_dir / templates.index_file_name).write_text(idx_content, encoding="utf-8")

    return generated
```

### Reference: `dispatcher.py` (only the types gendocs depends on)

```python
class CommandGroup(NamedTuple):
    name: str
    commands: Sequence[type[BaseCommand]]
    ordered: bool = False

class BaseCommand:
    name: str
    help_msg: str
    overview: str
    common: bool = False
    hidden: bool = False
    examples: list[tuple[str, str]] = []
    related_commands: list[str] | None = None

    def __init__(self, config: dict[str, Any] | None) -> None:
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        """Override to add command-specific arguments."""

    def run(self, parsed_args: argparse.Namespace) -> int | None:
        raise NotImplementedError
```

### Reference: Bundled reST command template

```jinja2
.. _ref_{{ ref }}:

{{ command_name }}
{{ '=' | repeat(heading_len) }}

{{ short }}

**Usage:**

.. code-block:: bash

   {{ synopsis }}

Overview
--------

{{ long }}

{% if flags %}
Options
-------

{% for flag in flags %}
.. option:: {{ flag.name }}

   {{ flag.usage | indent(3) }}
   {% if flag.default_value %}

   Default: ``{{ flag.default_value }}``
   {% endif %}

{% endfor %}
{% endif %}
{% if examples %}
Examples
--------

{% for example in examples %}
**{{ example.info }}**

.. code-block:: bash

   {{ example.usage }}

{% endfor %}
{% endif %}
{% if related_commands %}
See also
--------

{% for cmd in related_commands %}
- :ref:`{{ cmd }} <ref_{{ cmd | replace('-', '_') | replace(' ', '_') }}>`
{% endfor %}
{% endif %}
```

### Reference: Bundled reST index template

```jinja2
.. _cli_reference:

CLI Reference
=============

Command-line interface reference for **{{ appname }}**.

This reference documentation is automatically generated from the command
definitions and provides detailed information about each available command.

Available Commands
------------------

{% for group_name, group_files in files | groupby('group_name') %}
{{ group_name }}
{{ '~' | repeat(group_name | length) }}

.. toctree::
   :maxdepth: 1

{% for file in group_files %}
   {{ file.filename[:-4] }}
{% endfor %}

{% endfor %}

Quick Reference Table
---------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Command
     - Description
{% for file in files %}
   * - :ref:`{{ file.command_name }} <ref_{{ file.command_name | replace('-', '_') | replace(' ', '_') }}>`
     - {{ file.short }}
{% endfor %}
```

### Reference: Example generated output (`greet.rst`)

```rst
.. _ref_greet:

greet
=====

Greet a specific person

**Usage:**

.. code-block:: bash

   democli greet [--formal] [--enthusiasm ENTHUSIASM] [--suffix SUFFIX]
                     name

Overview
--------

The greet command allows you to personalize your greeting by specifying
a name. You can also customize the greeting style and add an optional
message suffix.

This command demonstrates how to use positional and optional arguments
with craft_cli.

Options
-------

.. option:: --formal

      Use formal greeting style

   Default: ``False``

.. option:: --enthusiasm

      Enthusiasm level (1-5)

   Default: ``1``

.. option:: --suffix

      Optional message suffix

Examples
--------

**Greet Alice**

.. code-block:: bash

   democli greet Alice

**Greet Bob formally**

.. code-block:: bash

   democli greet Bob --formal

**Greet Charlie with enthusiasm**

.. code-block:: bash

   democli greet Charlie --enthusiasm 5

**Greet multiple people**

.. code-block:: bash

   democli greet Alice --suffix ', have a great day!'

See also
--------

- :ref:`hello <ref_hello>`
- :ref:`farewell <ref_farewell>`
```

### Reference: Test suite (adapt for gencodo's Protocol-based interface)

```python
"""Unit tests for craft_cli.gendocs dataclasses."""

import argparse
import dataclasses
import io

import craft_cli
import jinja2.exceptions
import pytest
from craft_cli.dispatcher import BaseCommand, CommandGroup
from craft_cli.gendocs import (
    ExampleInfo,
    FlagInfo,
    TemplateInfo,
    _build_template_context,
    _extract_flags,
    _infer_related,
    _make_jinja_env,
    gen_docs,
    gen_docs_tree,
)

# --- Tests for FlagInfo

def test_flag_info_construction():
    fi = FlagInfo(name="--verbose", usage="Enable verbose output", default_value="false")
    assert fi.name == "--verbose"
    assert fi.usage == "Enable verbose output"
    assert fi.default_value == "false"

# --- Tests for ExampleInfo

def test_example_info_construction():
    ei = ExampleInfo(info="Build the project", usage="myapp build")
    assert ei.info == "Build the project"
    assert ei.usage == "myapp build"

# --- Tests for TemplateInfo

def test_template_info_valid_construction():
    ti = TemplateInfo(
        index_file_name="index.md",
        index_template="# Index\n",
        command_template="# {{ command_name }}\n",
    )
    assert ti.index_file_name == "index.md"

@pytest.mark.parametrize(
    ("index_file_name", "index_template", "command_template", "bad_field"),
    [
        ("", "tmpl", "cmd", "index_file_name"),
        ("file", "", "cmd", "index_template"),
        ("file", "tmpl", "", "command_template"),
    ],
)
def test_template_info_empty_field_raises(
    index_file_name, index_template, command_template, bad_field
):
    with pytest.raises(ValueError, match=f"TemplateInfo.{bad_field} must not be empty"):
        TemplateInfo(
            index_file_name=index_file_name,
            index_template=index_template,
            command_template=command_template,
        )

def test_template_info_whitespace_only_raises():
    with pytest.raises(ValueError, match="TemplateInfo.index_template must not be empty"):
        TemplateInfo(index_file_name="file", index_template="   ", command_template="cmd")

# --- Tests for frozen/hashable behavior

@pytest.mark.parametrize(
    "instance",
    [
        FlagInfo(name="--flag", usage="A flag", default_value="x"),
        ExampleInfo(info="An example", usage="cmd example"),
        TemplateInfo(index_file_name="idx.md", index_template="# Index", command_template="# Cmd"),
    ],
)
def test_dataclasses_are_frozen(instance):
    field_name = dataclasses.fields(instance)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, field_name, "new_value")

def test_dataclasses_support_equality():
    assert FlagInfo("a", "b", "c") == FlagInfo("a", "b", "c")
    assert ExampleInfo("info", "usage") == ExampleInfo("info", "usage")
    assert TemplateInfo("idx.md", "# Index", "# Cmd") == TemplateInfo("idx.md", "# Index", "# Cmd")

# --- Helper command classes (adapt to use Protocol/duck-typing for gencodo)
# ... (full test suite in reference material above)
```

---

## Design Decisions (Mandatory)

### 1. Protocol-based interface (no inheritance required)

Instead of requiring users to inherit from a base class, define `typing.Protocol` classes. Any existing command class with the right attributes/methods satisfies the protocol via structural subtyping:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Command(Protocol):
    """Protocol that any CLI command class must satisfy."""
    name: str
    help_msg: str
    overview: str
    hidden: bool
    examples: list[tuple[str, str]]          # (description, command_string)
    related_commands: list[str] | None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None: ...
```

Provide sensible defaults via a helper or document that `hidden` defaults to `False`, `examples` defaults to `[]`, `related_commands` defaults to `None`.

Also define:

```python
class CommandGroup(NamedTuple):
    name: str
    commands: Sequence[type[Command]]
```

**Important adaptation**: The original code does `command_class(None).fill_parser(parser)` to instantiate the command before calling `fill_parser`. Since gencodo uses a Protocol and users' command classes may have different constructors, gencodo must handle this differently. Options:
- Try calling `command_class(None)` and fall back to `command_class()` if that fails
- Or: accept that `fill_parser` may be a classmethod or standalone function
- **Recommended approach**: Try `command_class(None)` first (for craft_cli compatibility), then try `command_class()` (for simple classes), and document the expectation. This keeps the package compatible with both craft_cli apps and plain argparse apps.

### 2. Package structure

```
gencodo-py/
  src/
    gencodo/
      __init__.py          # Re-exports public API
      _core.py             # gen_docs, gen_docs_tree, _extract_flags, etc.
      _types.py            # ExampleInfo, FlagInfo, TemplateInfo, Command protocol, CommandGroup
      _jinja_env.py        # _make_jinja_env
      templates/           # Bundled default templates (package data)
        rst/
          command.rst.j2
          index.rst.j2
        md/
          command.md.j2
          index.md.j2
      py.typed             # PEP 561 marker
  tests/
    __init__.py
    test_types.py          # Tests for dataclasses, Protocol
    test_extract_flags.py  # Tests for flag extraction
    test_jinja_env.py      # Tests for Jinja2 environment
    test_infer_related.py  # Tests for related command inference
    test_build_context.py  # Tests for template context building
    test_gen_docs.py       # Tests for gen_docs()
    test_gen_docs_tree.py  # Tests for gen_docs_tree()
    conftest.py            # Shared fixtures (helper command classes)
  examples/
    demo_cli/
      app.py               # Example CLI app using plain argparse
      generate_docs.py     # Script showing how to use gencodo
  pyproject.toml
  README.md
  LICENSE
  CHANGELOG.md
```

### 3. Public API (re-exported from `gencodo.__init__`)

```python
__all__ = [
    "Command",
    "CommandGroup",
    "ExampleInfo",
    "FlagInfo",
    "TemplateInfo",
    "gen_docs",
    "gen_docs_tree",
    "get_bundled_templates",  # NEW: helper to load bundled templates
]
```

### 4. New helper: `get_bundled_templates()`

```python
def get_bundled_templates(
    format: Literal["rst", "md"] = "rst",
    index_file_name: str | None = None,
) -> TemplateInfo:
    """Load bundled default templates for the given format.

    Args:
        format: Template format - "rst" for reStructuredText, "md" for Markdown.
        index_file_name: Override the default index filename.
            Defaults to "index.rst" or "index.md" based on format.

    Returns:
        A TemplateInfo with the bundled templates loaded.
    """
```

### 5. Bundled Markdown templates (NEW - create these)

Create Markdown equivalents of the reST templates. The Markdown command template should produce output like:

```markdown
# greet

Greet a specific person

**Usage:**

```
democli greet [--formal] [--enthusiasm ENTHUSIASM] [--suffix SUFFIX] name
```

## Overview

The greet command allows you to personalize your greeting...

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--formal` | Use formal greeting style | `False` |
| `--enthusiasm` | Enthusiasm level (1-5) | `1` |
| `--suffix` | Optional message suffix | |

## Examples

**Greet Alice**

```
democli greet Alice
```

## See also

- [hello](hello.md)
- [farewell](farewell.md)
```

### 6. Packaging metadata (`pyproject.toml`)

- Build system: `hatchling` (or `setuptools` with `src` layout)
- Name: `gencodo-py`
- Import name: `gencodo`
- Version: `0.1.0`
- Python: `>=3.10`
- Dependencies: `jinja2>=3.0`
- Dev dependencies: `pytest>=7.0`, `pytest-cov`
- License: `LGPL-3.0-only`
- Author: (leave placeholder)
- Classifiers: appropriate PyPI classifiers for a documentation generation library
- Include `py.typed` marker and `templates/` as package data

### 7. Instantiation strategy for Protocol-based commands

The original does `command_class(None).fill_parser(parser)`. For the standalone package, implement this logic in a private helper:

```python
def _instantiate_command(command_class: type[Command]) -> Command:
    """Instantiate a command class for parser introspection.

    Tries command_class(None) first (craft_cli compatible),
    then command_class() for simple classes.
    """
    try:
        return command_class(None)  # type: ignore[call-arg]
    except TypeError:
        return command_class()  # type: ignore[call-arg]
```

---

## Constraints

1. **Zero runtime dependencies** besides `jinja2>=3.0`. No craft_cli dependency.
2. **Python >=3.10**. Use `X | Y` union syntax, `slots=True` in dataclasses.
3. **src layout** with `src/gencodo/`.
4. All public classes and functions must have docstrings.
5. The test suite must be comprehensive - port ALL tests from the reference test suite, adapting them to use Protocol-satisfying command classes instead of BaseCommand subclasses.
6. Tests must be runnable with just `pytest` from the project root.
7. **Keep examples and related_commands** in the Protocol and template context.
8. Do NOT include a CLI entry point. Library-only.
9. Template files must be loadable via `importlib.resources` (Python 3.10+).
10. Use `__all__` in `__init__.py` to control the public API.

---

## Output Requirements

Produce every file listed in the package structure above, complete and ready to use. For each file, output:

```
=== FILE: <relative_path> ===
<complete file content>
```

### Specific file requirements:

1. **`pyproject.toml`**: Complete with build system, metadata, dependencies, optional dev deps, tool config for pytest.
2. **`src/gencodo/__init__.py`**: Re-export all public symbols with `__all__`, include `__version__`.
3. **`src/gencodo/_types.py`**: `Command` Protocol, `CommandGroup` NamedTuple, `ExampleInfo`, `FlagInfo`, `TemplateInfo` dataclasses.
4. **`src/gencodo/_jinja_env.py`**: `_make_jinja_env()` function.
5. **`src/gencodo/_core.py`**: All generation logic: `_instantiate_command`, `_extract_flags`, `_infer_related`, `_build_template_context`, `gen_docs`, `gen_docs_tree`, `get_bundled_templates`.
6. **`src/gencodo/templates/rst/command.rst.j2`**: The reST command template from reference material.
7. **`src/gencodo/templates/rst/index.rst.j2`**: The reST index template from reference material.
8. **`src/gencodo/templates/md/command.md.j2`**: NEW Markdown command template.
9. **`src/gencodo/templates/md/index.md.j2`**: NEW Markdown index template.
10. **`src/gencodo/py.typed`**: Empty PEP 561 marker.
11. **`tests/conftest.py`**: Shared fixtures with helper command classes that satisfy the `Command` Protocol using plain classes (no BaseCommand inheritance).
12. **`tests/test_types.py`**: Tests for dataclasses (frozen, equality, hashable, validation).
13. **`tests/test_extract_flags.py`**: Tests for `_extract_flags`.
14. **`tests/test_jinja_env.py`**: Tests for `_make_jinja_env`.
15. **`tests/test_infer_related.py`**: Tests for `_infer_related`.
16. **`tests/test_build_context.py`**: Tests for `_build_template_context`.
17. **`tests/test_gen_docs.py`**: Tests for `gen_docs()`.
18. **`tests/test_gen_docs_tree.py`**: Tests for `gen_docs_tree()`.
19. **`tests/test_bundled_templates.py`**: Tests for `get_bundled_templates()` and that bundled templates render without error.
20. **`examples/demo_cli/app.py`**: A simple multi-command CLI app using plain argparse classes (NOT craft_cli).
21. **`examples/demo_cli/generate_docs.py`**: Script demonstrating gencodo usage with the demo app.
22. **`README.md`**: Project README with installation, quick start, API reference summary, template customization guide.
23. **`LICENSE`**: LGPL-3.0 license text.
24. **`CHANGELOG.md`**: Initial changelog entry for v0.1.0.

---

## Verification Checklist

After producing all files, verify:

- [ ] `Command` Protocol defines: `name`, `help_msg`, `overview`, `hidden`, `examples`, `related_commands`, `fill_parser()`
- [ ] `CommandGroup` is a NamedTuple with `name` and `commands` fields
- [ ] `_instantiate_command` tries `(None)` then `()` fallback
- [ ] `_extract_flags` skips positionals and SUPPRESS'd flags, uses longest option string as name
- [ ] `_infer_related` validates explicit names, infers from siblings when None, excludes hidden
- [ ] `_build_template_context` returns all 10 keys: ref, command_name, short, long, synopsis, examples, flags, related_commands, heading_len, appname
- [ ] `gen_docs` writes to TextIO, does NOT flush
- [ ] `gen_docs_tree` creates output_dir, skips hidden commands, returns command filenames (not index)
- [ ] `get_bundled_templates` loads from package data for both "rst" and "md"
- [ ] Bundled reST templates match the reference output
- [ ] Bundled Markdown templates produce clean, valid Markdown
- [ ] All test classes use Protocol-satisfying plain classes, not BaseCommand
- [ ] Tests cover: dataclass behavior, flag extraction, env configuration, related inference, context building, single-doc gen, tree gen, bundled templates
- [ ] `pyproject.toml` is valid with correct build system, deps, and package data inclusion
- [ ] `__init__.py` exports all 8 public symbols via `__all__`
- [ ] Example app works as a standalone demonstration without craft_cli
