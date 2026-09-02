<!-- SPDX-License-Identifier: LGPL-3.0-only -->
<!-- Copyright 2026 Canonical Ltd. -->

# gencodo-py

Generate CLI reference documentation from argparse-based applications using Jinja2 templates.

gencodo-py is the Python sibling of [gencodo](https://github.com/canonical/gencodo) (Go, for Cobra).
It extracts structured data from command classes (description, usage, positional arguments,
options, examples, related commands) and renders it through templates you control, so the output
can be reStructuredText, Markdown, or any other text format. Command classes only need a few
attributes and a `fill_parser` method; [craft-cli](https://github.com/canonical/craft-cli) commands
satisfy the protocol as they are.

## Installation

```bash
pip install gencodo-py
```

## Quick Start

Define your CLI commands as plain Python classes (no base class required):

```python
import argparse

class GreetCommand:
    name = "greet"
    help_msg = "Greet a specific person"
    overview = "Personalize your greeting by specifying a name."
    hidden = False
    examples = [("Greet Alice", "myapp greet Alice")]
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("name", help="Name to greet")
        parser.add_argument("-f", "--formal", action="store_true", help="Use formal style")
```

Generate documentation:

```python
from gencodo import CommandGroup, gen_docs_tree, get_bundled_templates

groups = [CommandGroup(name="Greetings", commands=[GreetCommand])]
templates = get_bundled_templates("md")  # or "rst"

gen_docs_tree(
    appname="myapp",
    command_groups=groups,
    output_dir="docs/cli-ref",
    templates=templates,
)
```

See `examples/demo_cli/` for a complete demo application and its generated output in both formats.

## API Reference

### Types

- **`Command`** -- Protocol that any CLI command class must satisfy (structural subtyping).
- **`CommandClass`** -- Alias for `type[Command]`.
- **`CommandGroup`** -- NamedTuple grouping commands under a name.
- **`ExampleInfo`** -- Dataclass for a usage example (`info`, `usage`).
- **`ArgumentInfo`** -- Dataclass for a positional argument (`name`, `usage`, `metavar`, `nargs`, `choices`, `default_value`).
- **`FlagInfo`** -- Dataclass for an optional argument (`name`, `short`, `option_strings`, `usage`, `default_value`, `metavar`, `choices`, `required`, `is_flag`).
- **`TemplateInfo`** -- Dataclass for Jinja2 template configuration (`index_file_name`, `index_template`, `command_template`).

### Functions

- **`gen_docs(command_class, writer, template, appname, command_groups, command_config=None, *, extra_filters=None)`** -- Render docs for a single command to a text stream.
- **`gen_docs_tree(appname, command_groups, output_dir, templates, file_prepender=None, file_extension=".md", command_config=None, *, file_prefix="", extra_filters=None, dry_run=False)`** -- Generate a full documentation tree (one file per non-hidden command, plus the index). Returns the command file names. Every page is rendered before anything is written, so a template error leaves no partial output.
- **`validate_templates(templates, *, appname="app", extra_filters=None)`** -- Render both templates against synthetic data without touching the file system. Raises the same Jinja2 errors generation would.
- **`get_bundled_templates(format="rst", index_file_name=None)`** -- Load the bundled reST or Markdown templates.

Parameters worth knowing:

| Parameter | Purpose |
|-----------|---------|
| `command_config` | Passed as the sole constructor argument to every command class (craft-cli passes its app config this way). Without it, gencodo tries `cls(None)` and then `cls()`. |
| `file_prefix` | Prefix for command file names, e.g. `"myapp-"` produces `myapp-greet.rst`. |
| `file_prepender` | `Callable[[str], str]` whose result is written at the top of each file; receives the file name. Use it for banners or front matter. |
| `extra_filters` | Mapping of extra Jinja2 filters. Names that clash with built-ins override them. Pass the same mapping to `validate_templates`. |
| `dry_run` | Render everything, write nothing. Combine with your real command groups to validate templates in CI. |

### Command Protocol

Your command classes need these attributes/methods:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Command name |
| `help_msg` | `str` | Short help string |
| `hidden` | `bool` | Exclude from docs if True |
| `fill_parser(parser)` | method | Add arguments to an `ArgumentParser` |

Optional attributes, read with `getattr`:

| Attribute | Type | Description |
|-----------|------|-------------|
| `overview` | `str` | Longer description (rendered as `long`) |
| `examples` | `list[tuple[str, str]]` | (description, command) pairs |
| `related_commands` | `list[str] \| None` | Explicit related commands, or `None` to list the non-hidden siblings in the same group |
| `common` | `bool` | craft-cli's "common command" marker, exposed as `common` |

## Templates

Templates are [Jinja2](https://jinja.palletsprojects.com/) with `trim_blocks`, `lstrip_blocks`,
`keep_trailing_newline`, and `StrictUndefined`: a typo in a variable name fails generation rather
than rendering an empty string.

### Bundled templates

`get_bundled_templates("rst")` and `get_bundled_templates("md")` return the templates under
`src/gencodo/templates/`. They render usage, overview, arguments, options (with short forms,
choices, required markers, and defaults), examples, and related commands; the reST index groups
commands in a `toctree` and a quick-reference table, the Markdown index uses lists and a table.

### Custom templates

Pass your own template strings via `TemplateInfo`:

```python
from gencodo import TemplateInfo, validate_templates

templates = TemplateInfo(
    index_file_name="index.md",
    index_template="# Commands\n{% for f in files %}- [{{ f.command_name }}]({{ f.filename }})\n{% endfor %}",
    command_template="# {{ command_name }}\n\n{{ short }}\n",
)
validate_templates(templates)  # fails fast on unknown variables or filters
```

### Command template variables

| Variable | Type | Description |
|----------|------|-------------|
| `command_name` | `str` | Command name |
| `ref` | `str` | Anchor-friendly name (dashes and spaces to underscores) |
| `filename` | `str` | This command's output file name (with `file_prefix` and extension) |
| `short` | `str` | Short help message |
| `long` | `str` | Overview text, stripped |
| `synopsis` | `str` | Single-line usage, e.g. `myapp greet [-f] name` |
| `heading_len` | `int` | Length of `command_name`, for underlines |
| `arguments` | `list[ArgumentInfo]` | Positional arguments in declaration order |
| `flags` | `list[FlagInfo]` | Optional arguments in declaration order (suppressed ones excluded) |
| `examples` | `list[ExampleInfo]` | Usage examples |
| `related_commands` | `list[str]` | Related command names |
| `appname` | `str` | Application name |
| `group_name` | `str` | Name of the command's group |
| `hidden`, `common` | `bool` | The command's flags of the same name |

### Index template variables

| Variable | Type | Description |
|----------|------|-------------|
| `appname` | `str` | Application name |
| `files` | `list[dict]` | One entry per generated page: `filename`, `command_name`, `short`, `group_name`, `ref` |
| `commands` | `list[dict]` | Alias of `files` |

Group with `{% for group_name, entries in files | groupby('group_name') %}`.

### Filters

In addition to Jinja2's built-ins (`replace`, `join`, `lower`, `upper`, `trim`, `groupby`, ...):

| Filter | Example | Result |
|--------|---------|--------|
| `indent(width, first=True, blank=False)` | `{{ usage \| indent(3) }}` | Indents every line (first line included by default; `first=False` when the template already indents it) |
| `repeat(n)` | `{{ '=' \| repeat(heading_len) }}` | Repeats a string |
| `slug` | `{{ 'My App sub!' \| slug }}` | `my-app-sub` |
| `anchor` | `{{ 'ref_my app' \| anchor }}` | `ref_my-app` (keeps underscores) |
| `title_case` | `{{ 'list all' \| title_case }}` | `List All` |
| `trim_prefix(p)` / `trim_suffix(p)` | `{{ short \| trim_suffix('.') }}.` | Exactly one trailing period |
| `replace_spaces(r='_')` | `{{ command_name \| replace_spaces }}` | `my_command` |

Add your own with `extra_filters`.

### Link patterns

- reST: label each page with `.. _ref_{{ ref }}:` and link with ``:ref:`{{ cmd }} <ref_{{ cmd | replace('-', '_') }}>` ``; the index can `.. include::` or `toctree` the `filename` entries.
- Markdown: link siblings by file name, `[{{ cmd }}]({{ file_prefix }}{{ cmd }}.md)`, or by heading anchor with `slug`.

## Behaviour notes

- Hidden commands are skipped by `gen_docs_tree` and by related-command inference.
- Options with `help=argparse.SUPPRESS` are omitted; explicit `related_commands` names are validated against all groups and raise `ValueError` if unknown.
- `synopsis` comes from argparse's usage formatter with an unlimited width, so it is one line.
- `default_value` is empty for `None`, `argparse.SUPPRESS`, and value-less actions (`store_true`, `store_false`, `count`); check `is_flag` to decide whether to show a default at all.
- Command classes are instantiated once per page to fill a throwaway parser; craft-application's parse callbacks run as part of `fill_parser`.

## Development

```bash
make install        # uv sync --group dev
make                # ruff, mypy, pytest
make test-coverage  # coverage report (htmlcov/)
make reuse          # REUSE license/copyright compliance
make examples       # regenerate examples/demo_cli/docs_output (CI checks it is current)
```

CI runs the tests on Python 3.10 to 3.14, ruff, mypy, REUSE, a build, and the example-output check.

## Release process (maintainers)

1. Set `__version__` in `src/gencodo/__init__.py` (the only place the version lives) and move the
   `[Unreleased]` entries in `CHANGELOG.md` into a `## [X.Y.Z] - YYYY-MM-DD` section; update the compare links.
2. Commit, then run `make release VERSION=vX.Y.Z`. It checks the version and CHANGELOG, runs the checks, tags, and pushes the tag.
3. The `Publish to PyPI` workflow builds, publishes through PyPI trusted publishing (environment `pypi`), and creates
   the GitHub release with the CHANGELOG section as notes; check `gh release view vX.Y.Z` and `pip index versions gencodo-py`.

## License and copyright

gencodo-py is licensed under the [LGPL-3.0-only](LICENSES/LGPL-3.0-only.txt) and follows the
[REUSE](https://reuse.software) specification: every file carries SPDX license and copyright
information, either in a header or through `REUSE.toml` for files that cannot hold a comment.
`make reuse` and the CI `reuse` job verify this.
