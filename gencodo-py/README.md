# gencodo-py

Generate CLI reference documentation from argparse-based applications using Jinja2 templates.

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
        parser.add_argument("--formal", action="store_true", default=False,
                            help="Use formal style")
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

## API Reference

### Types

- **`Command`** -- Protocol that any CLI command class must satisfy (structural subtyping).
- **`CommandGroup`** -- NamedTuple grouping commands under a name.
- **`ExampleInfo`** -- Dataclass for a usage example (info, usage).
- **`FlagInfo`** -- Dataclass for a CLI flag (name, usage, default_value).
- **`TemplateInfo`** -- Dataclass for Jinja2 template configuration.

### Functions

- **`gen_docs(command_class, writer, template, appname, command_groups)`** -- Render docs for a single command to a TextIO writer.
- **`gen_docs_tree(appname, command_groups, output_dir, templates, ...)`** -- Generate a full documentation tree (one file per command + index).
- **`get_bundled_templates(format="rst", index_file_name=None)`** -- Load bundled reST or Markdown templates.

### Command Protocol

Your command classes need these attributes/methods:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Command name |
| `help_msg` | `str` | Short help string |
| `overview` | `str` | Longer description |
| `hidden` | `bool` | Exclude from docs if True |
| `examples` | `list[tuple[str, str]]` | (description, command) pairs |
| `related_commands` | `list[str] \| None` | Explicit related commands, or None to auto-infer |
| `fill_parser(parser)` | method | Add arguments to an ArgumentParser |

## Template Customization

### Bundled Templates

Use `get_bundled_templates("rst")` or `get_bundled_templates("md")` for the built-in templates.

### Custom Templates

Pass your own Jinja2 template strings via `TemplateInfo`:

```python
from gencodo import TemplateInfo

templates = TemplateInfo(
    index_file_name="index.md",
    index_template="# Commands\n{% for f in files %}...\n{% endfor %}",
    command_template="# {{ command_name }}\n{{ short }}\n...",
)
```

Available template variables for command templates:

| Variable | Type | Description |
|----------|------|-------------|
| `ref` | `str` | Anchor reference (underscored name) |
| `command_name` | `str` | Command name |
| `short` | `str` | Short help message |
| `long` | `str` | Overview text |
| `synopsis` | `str` | Usage synopsis |
| `examples` | `list[ExampleInfo]` | Usage examples |
| `flags` | `list[FlagInfo]` | Optional flags |
| `related_commands` | `list[str]` | Related command names |
| `heading_len` | `int` | Length of command name |
| `appname` | `str` | Application name |

Custom Jinja2 filters available: `indent(width)`, `repeat(n)`.

## License

LGPL-3.0-only
