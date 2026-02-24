# Changelog

## 0.1.0

Initial release.

- Protocol-based `Command` interface (no inheritance required)
- `gen_docs()` for single-command documentation
- `gen_docs_tree()` for full documentation trees
- `get_bundled_templates()` with reST and Markdown formats
- Jinja2-based template rendering with `indent` and `repeat` filters
- `ExampleInfo`, `FlagInfo`, `TemplateInfo` dataclasses
- `CommandGroup` named tuple for organizing commands
- Automatic related-command inference from sibling commands
- PEP 561 type stubs (`py.typed`)
