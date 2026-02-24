# Demo CLI Application - craft_cli Documentation Generation Showcase

This demo application showcases how to use craft_cli's documentation generation capabilities to automatically create CLI reference documentation in reStructuredText format.

## Overview

The demo consists of:

1. **demo_cli.py** - A simple CLI application with several commands demonstrating craft_cli features
2. **generate_docs.py** - A harness script that uses `craft_cli.gendocs` to generate documentation
3. **templates/** - ReStructuredText Jinja2 templates for command and index pages
4. **docs_generated/** - Output directory containing the generated .rst files

## Commands in the Demo

The demo CLI includes several representative commands:

- `hello` - A simple command with no arguments
- `greet` - A command with positional and optional arguments
- `farewell` - A command with multiple choice options
- `list-items` - A command with filtering, search, and format options
- `debug` - A hidden command (excluded from generated docs)

## How Documentation Generation Works

The documentation generation process:

1. **Define Commands** - Create command classes inheriting from `BaseCommand`

    - Set `name`, `help_msg`, `overview` attributes
    - Add `examples` as a list of (description, usage) tuples
    - Set `related_commands` for cross-references (or use None to auto-infer)

2. **Create Templates** - Write Jinja2 templates in reStructuredText

    - Command template receives: `command_name`, `short`, `long`, `synopsis`, `examples`, `flags`, `related_commands`, etc.
    - Index template receives: `appname` and `files` (list of command metadata)

3. **Generate Documentation** - Use `gen_docs_tree()`

    ```python
    from craft_cli.gendocs import TemplateInfo, gen_docs_tree

    templates = TemplateInfo(
        index_file_name="index.rst",
        index_template=index_template_string,
        command_template=command_template_string,
    )

    generated_files = gen_docs_tree(
        appname="democli",
        command_groups=COMMAND_GROUPS,
        output_dir=output_path,
        templates=templates,
        file_extension=".rst",
    )
    ```

## Running the Demo

### Generate Documentation

From the `demo_app` directory:

```bash
# Make sure you're using the virtual environment
cd /path/to/craft-cli-akcano
source .venv/bin/activate

# Generate the documentation
cd demo_app
python generate_docs.py [output_directory]
```

### Run the CLI Application

```bash
# From the demo_app directory
python demo_cli.py --help
python demo_cli.py hello
python demo_cli.py greet Alice --formal
```

## Generated Documentation Structure

The generated documentation includes:

- **index.rst** - Main index with command groups and quick reference table
- **hello.rst** - Command page with usage, overview, examples
- **greet.rst** - Command page with options and cross-references
- **farewell.rst** - Command page with choice-based options
- **list-items.rst** - Command page with complex filtering options

Each command page includes:

- Reference label for cross-linking
- Command name as heading
- One-line description
- Usage synopsis with argument parser format
- Overview section with detailed description
- Options section (if flags are defined)
- Examples section with code blocks
- See also section with related command links

## Key Features Demonstrated

1. **Automatic synopsis generation** - Uses argparse to create usage strings
2. **Flag extraction** - Automatically documents all command-line options
3. **Example formatting** - Converts example tuples to formatted code blocks
4. **Cross-references** - Creates reST links between related commands
5. **Hidden commands** - Excludes commands marked `hidden=True`
6. **Multi-word commands** - Handles command names with spaces
7. **Command grouping** - Organizes commands by CommandGroup in index

## Template Customization

The reST templates use Jinja2 with custom filters:

- `repeat(n)` - Repeats a string n times (for reST underlines)
- `indent(width)` - Indents all lines including first
- Standard filters: `length`, `replace`, `groupby`

You can customize the templates to:

- Change heading styles (use different reST markers)
- Add custom sections
- Format examples differently
- Include additional metadata
- Adjust cross-reference formats

## Integration with Sphinx

To integrate with a Sphinx documentation project:

1. Copy generated .rst files to your Sphinx source directory
2. Add the index file to your main toctree:

    ```rst
    .. toctree::
       :maxdepth: 2

       cli-reference/index
    ```

3. Build with Sphinx: `sphinx-build -b html source build`

## Files

```
demo_app/
├── README.md                    # This file
├── demo_cli.py                  # Demo CLI application
├── generate_docs.py             # Documentation generation harness
├── templates/
│   ├── command_template.rst     # Jinja2 template for command pages
│   └── index_template.rst       # Jinja2 template for index page
└── docs_generated/
    ├── index.rst                # Generated index
    ├── hello.rst                # Generated command doc
    ├── greet.rst                # Generated command doc
    ├── farewell.rst             # Generated command doc
    └── list-items.rst           # Generated command doc
```
