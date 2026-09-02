<!-- SPDX-License-Identifier: LGPL-3.0-only -->
<!-- Copyright 2026 Canonical Ltd. -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
While the major version is 0, minor releases may change behaviour; such changes are
called out under **Changed** or marked **BREAKING**.

## [Unreleased]

## [0.4.0] - 2026-09-02

### Added
- Positional arguments are exposed to templates as `arguments` (`ArgumentInfo`: name, usage, metavar, nargs, choices, default); previously only optional flags were documented
- `FlagInfo` gained `short`, `option_strings`, `metavar`, `choices`, `required`, and `is_flag`, so templates can render `-o, --output PATH` and required or value-less options
- `validate_templates()` renders both templates against synthetic data (a fully populated and a minimal command) without writing files, for use in unit tests and CI
- `gen_docs_tree(..., file_prefix=...)` to name command pages `myapp-<command>.<ext>`; `dry_run=True` to render without writing
- `extra_filters=` on `gen_docs`, `gen_docs_tree`, and `validate_templates`; `BUILTIN_FILTERS` exported
- Jinja2 filters `slug`, `anchor`, `title_case`, `trim_prefix`, `trim_suffix`, `replace_spaces`; `indent` accepts `first=False`
- Command context gained `hidden`, `common`, `group_name`, and `filename`; index entries gained `ref` and the list is also available as `commands`
- CI: tests on Python 3.10–3.14 with coverage, ruff, mypy, REUSE, build, and an up-to-date check of the demo output; pre-commit configuration; `Makefile` (`make lint typecheck test reuse examples release`)
- REUSE compliance: `LICENSE`, `LICENSES/LGPL-3.0-only.txt`, `REUSE.toml`, SPDX headers on every file
- Release automation: pushing a `vX.Y.Z` tag verifies `__version__` and the CHANGELOG section, publishes to PyPI, and creates the GitHub release with those notes

### Changed
- `synopsis` is always a single line (argparse's terminal-width wrapping no longer leaks into code blocks)
- `FlagInfo.default_value` is empty for value-less actions (`store_true`, `store_false`, `count`), so pages no longer show `Default: False`
- Bundled templates: an *Arguments* section, `-s, --long METAVAR` option headings, `(required)` and *Choices*, the option body is indented once (was double-indented in reST), and the `Default:` line is a separate paragraph
- `gen_docs_tree` renders every page before writing anything, so a template error leaves no partial output
- The version is defined once, in `gencodo.__version__`, and read by hatchling; `pyproject.toml` and `__version__` had drifted (0.3.0 vs 0.2.0)
- Development dependencies moved to a PEP 735 `dev` dependency group (`uv sync --group dev`); the `dev` extra is gone
- Authors are now Canonical Ltd.; Python 3.14 added to the classifiers
- Pinned GitHub Actions bumped (checkout v7.0.1, setup-python v7.0.0, upload-artifact v7.0.1, zizmor v0.6.3, pypi-publish v1.14.2); Bandit failures now fail the SAST workflow instead of being ignored

### Removed
- `fix-gendocs-typing.md`, a leftover task prompt

## [0.3.0] - 2026-02-25

### Changed
- Tooling only: pinned GitHub Actions, SAST workflow (Bandit, zizmor), Renovate configuration, `# nosec` on the Jinja2 environment. No library changes.

## [0.2.0] - 2026-02-25

### Added
- `CommandClass` protocol alias for structural typing of command classes; `CommandGroup.commands` is a `Sequence[type[Command]]` so craft-cli command classes type-check without casts (#4)

### Changed
- `Command` protocol no longer declares `fill_parser`, whose signature craft-cli narrows to a private parser subclass

## [0.1.1] - 2026-02-24

### Added
- `command_config` parameter on `gen_docs` and `gen_docs_tree`, passed as the sole constructor argument to command classes (craft-cli style)

### Fixed
- Compiled Python files removed from the repository and ignored

## [0.1.0] - 2026-02-24

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

[Unreleased]: https://github.com/canonical/gencodo-py/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/canonical/gencodo-py/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/canonical/gencodo-py/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/canonical/gencodo-py/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/canonical/gencodo-py/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/canonical/gencodo-py/releases/tag/v0.1.0
