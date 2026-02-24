# Copyright 2021-2022 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

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
    """Construct FlagInfo and verify all fields are readable."""
    fi = FlagInfo(
        name="--verbose", usage="Enable verbose output", default_value="false"
    )
    assert fi.name == "--verbose"
    assert fi.usage == "Enable verbose output"
    assert fi.default_value == "false"


# --- Tests for ExampleInfo


def test_example_info_construction():
    """Construct ExampleInfo and verify all fields are readable."""
    ei = ExampleInfo(info="Build the project", usage="myapp build")
    assert ei.info == "Build the project"
    assert ei.usage == "myapp build"


# --- Tests for TemplateInfo


def test_template_info_valid_construction():
    """Construct TemplateInfo with valid fields and verify all fields are readable."""
    ti = TemplateInfo(
        index_file_name="index.md",
        index_template="# Index\n",
        command_template="# {{ command_name }}\n",
    )
    assert ti.index_file_name == "index.md"
    assert ti.index_template == "# Index\n"
    assert ti.command_template == "# {{ command_name }}\n"


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
    """Empty string for any TemplateInfo field raises ValueError naming that field."""
    with pytest.raises(ValueError, match=f"TemplateInfo.{bad_field} must not be empty"):
        TemplateInfo(
            index_file_name=index_file_name,
            index_template=index_template,
            command_template=command_template,
        )


def test_template_info_whitespace_only_raises():
    """Whitespace-only string for a TemplateInfo field raises ValueError."""
    with pytest.raises(
        ValueError, match="TemplateInfo.index_template must not be empty"
    ):
        TemplateInfo(
            index_file_name="file",
            index_template="   ",
            command_template="cmd",
        )


# --- Tests for frozen/hashable behavior across all three dataclasses


@pytest.mark.parametrize(
    "instance",
    [
        FlagInfo(name="--flag", usage="A flag", default_value="x"),
        ExampleInfo(info="An example", usage="cmd example"),
        TemplateInfo(
            index_file_name="idx.md",
            index_template="# Index",
            command_template="# Cmd",
        ),
    ],
)
def test_dataclasses_are_frozen(instance):
    """Assignment after construction raises FrozenInstanceError."""
    field_name = dataclasses.fields(instance)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, field_name, "new_value")


def test_dataclasses_support_equality():
    """Two instances constructed with equal args are equal."""
    assert FlagInfo("a", "b", "c") == FlagInfo("a", "b", "c")
    assert ExampleInfo("info", "usage") == ExampleInfo("info", "usage")
    assert TemplateInfo("idx.md", "# Index", "# Cmd") == TemplateInfo(
        "idx.md", "# Index", "# Cmd"
    )


def test_dataclasses_are_hashable():
    """Instances are usable as dict keys and set members."""
    fi = FlagInfo("--flag", "A flag", "x")
    ei = ExampleInfo("An example", "cmd example")
    ti = TemplateInfo("idx.md", "# Index", "# Cmd")

    s = {fi, ei}
    assert fi in s
    assert ei in s

    d = {ti: "value"}
    assert d[ti] == "value"


# ---------------------------------------------------------------------------
# Helper command classes for _extract_flags tests
# ---------------------------------------------------------------------------


class _BasicFlagCommand(BaseCommand):
    name = "basic"
    help_msg = "A basic command"
    overview = "Basic command overview."

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
        parser.add_argument("--output", metavar="FILE", help="Output file path")

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _PositionalCommand(BaseCommand):
    name = "positional"
    help_msg = "A command with a positional argument"
    overview = "Positional command overview."

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("target", help="The target")
        parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _SuppressedCommand(BaseCommand):
    name = "suppressed"
    help_msg = "A command with a suppressed flag"
    overview = "Suppressed command overview."

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--visible", help="A visible flag")
        parser.add_argument("--hidden-flag", help=argparse.SUPPRESS)

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _EmptyCommand(BaseCommand):
    name = "empty"
    help_msg = "A command with no flags"
    overview = "Empty command overview."

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _DefaultValueCommand(BaseCommand):
    name = "defaults"
    help_msg = "A command testing default values"
    overview = "Defaults command overview."

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--none-default", help="Defaults to None")
        parser.add_argument("--false-default", action="store_true", help="Defaults to False")
        parser.add_argument("--str-default", default="foo", help="Defaults to foo")
        parser.add_argument("--suppress-default", default=argparse.SUPPRESS, help="Suppress default")

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _ShortLongCommand(BaseCommand):
    name = "shortlong"
    help_msg = "A command with short and long options"
    overview = "Short/long command overview."

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


# --- Tests for _extract_flags


def test_extract_flags_basic():
    """Basic flag extraction returns FlagInfo for each optional flag."""
    flags = _extract_flags(_BasicFlagCommand)
    names = [f.name for f in flags]
    assert "--verbose" in names
    assert "--output" in names
    assert len(flags) == 2

    verbose_flag = next(f for f in flags if f.name == "--verbose")
    assert verbose_flag.usage == "Enable verbose output"
    assert verbose_flag.default_value == "False"

    output_flag = next(f for f in flags if f.name == "--output")
    assert output_flag.usage == "Output file path"
    assert output_flag.default_value == ""


def test_extract_flags_positionals_skipped():
    """Positional arguments are not included in the result list."""
    flags = _extract_flags(_PositionalCommand)
    names = [f.name for f in flags]
    assert "target" not in names
    assert "--verbose" in names
    assert len(flags) == 1


def test_extract_flags_suppressed_skipped():
    """Flags with help=argparse.SUPPRESS are not included in the result list."""
    flags = _extract_flags(_SuppressedCommand)
    names = [f.name for f in flags]
    assert "--hidden-flag" not in names
    assert "--visible" in names
    assert len(flags) == 1


def test_extract_flags_no_help_flag():
    """The --help flag is not included in the result (add_help=False)."""
    flags = _extract_flags(_BasicFlagCommand)
    names = [f.name for f in flags]
    assert "--help" not in names


def test_extract_flags_empty():
    """A command with no flags returns an empty list."""
    flags = _extract_flags(_EmptyCommand)
    assert flags == []


def test_extract_flags_default_values():
    """Default values are formatted correctly: None -> '', SUPPRESS -> '', real values -> str."""
    flags = _extract_flags(_DefaultValueCommand)
    flag_map = {f.name: f for f in flags}

    assert flag_map["--none-default"].default_value == ""
    assert flag_map["--false-default"].default_value == "False"
    assert flag_map["--str-default"].default_value == "foo"
    assert flag_map["--suppress-default"].default_value == ""


def test_extract_flags_longest_option_string_as_name():
    """When a flag has both short and long option strings, the longest is used as name."""
    flags = _extract_flags(_ShortLongCommand)
    assert len(flags) == 1
    assert flags[0].name == "--verbose"


# ---------------------------------------------------------------------------
# Tests for _make_jinja_env
# ---------------------------------------------------------------------------


def test_make_jinja_env_strict_undefined():
    """Rendering a template with a missing variable raises UndefinedError."""
    env = _make_jinja_env()
    template = env.from_string("Hello {{ missing_var }}!")
    with pytest.raises(jinja2.exceptions.UndefinedError):
        template.render()


def test_make_jinja_env_autoescape_false():
    """The environment has autoescape disabled."""
    env = _make_jinja_env()
    assert env.autoescape is False


def test_make_jinja_env_trim_and_lstrip_blocks():
    """The environment has trim_blocks and lstrip_blocks enabled."""
    env = _make_jinja_env()
    assert env.trim_blocks is True
    assert env.lstrip_blocks is True


def test_make_jinja_env_keep_trailing_newline():
    """The environment has keep_trailing_newline enabled."""
    env = _make_jinja_env()
    assert env.keep_trailing_newline is True


def test_make_jinja_env_indent_filter_all_lines():
    """The indent filter indents all lines including the first."""
    env = _make_jinja_env()
    result = env.filters["indent"]("line1\nline2", 4)
    assert result == "    line1\n    line2"


def test_make_jinja_env_indent_filter_single_line():
    """The indent filter indents a single line."""
    env = _make_jinja_env()
    result = env.filters["indent"]("single", 2)
    assert result == "  single"


def test_make_jinja_env_repeat_filter():
    """The repeat filter multiplies a string N times."""
    env = _make_jinja_env()
    assert env.filters["repeat"]("=", 5) == "====="
    assert env.filters["repeat"]("ab", 3) == "ababab"


# ---------------------------------------------------------------------------
# Helper command classes for _infer_related and _build_template_context tests
# ---------------------------------------------------------------------------


class _CommandA(BaseCommand):
    name = "alpha"
    help_msg = "Alpha command"
    overview = "Alpha overview."
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _CommandB(BaseCommand):
    name = "beta"
    help_msg = "Beta command"
    overview = "Beta overview."
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _CommandC(BaseCommand):
    name = "gamma"
    help_msg = "Gamma command"
    overview = "Gamma overview."
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _HiddenCommand(BaseCommand):
    name = "hidden-cmd"
    help_msg = "Hidden command"
    overview = "Hidden overview."
    hidden = True
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _ExplicitRelatedCommand(BaseCommand):
    name = "build"
    help_msg = "Build command"
    overview = "Build overview."
    related_commands = ["alpha", "beta"]

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _BadRelatedCommand(BaseCommand):
    name = "bad"
    help_msg = "Bad command"
    overview = "Bad overview."
    related_commands = ["nonexistent"]

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _EmptyRelatedCommand(BaseCommand):
    name = "solo"
    help_msg = "Solo command"
    overview = "Solo overview."
    related_commands = []

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


# --- Tests for _infer_related


def test_infer_related_explicit_returned_as_is():
    """Explicit related_commands returned unchanged when all names exist."""
    group = CommandGroup(name="grp", commands=[_ExplicitRelatedCommand, _CommandA, _CommandB])
    result = _infer_related(_ExplicitRelatedCommand, [group])
    assert result == ["alpha", "beta"]


def test_infer_related_explicit_invalid_name_raises():
    """Explicit related_commands with non-existent name raises ValueError."""
    group = CommandGroup(name="grp", commands=[_BadRelatedCommand, _CommandA])
    with pytest.raises(ValueError, match="nonexistent"):
        _infer_related(_BadRelatedCommand, [group])


def test_infer_related_infers_siblings():
    """When related_commands is None, returns sorted non-hidden sibling names."""
    group = CommandGroup(name="grp", commands=[_CommandA, _CommandB, _CommandC])
    result = _infer_related(_CommandA, [group])
    assert result == ["beta", "gamma"]


def test_infer_related_excludes_hidden_siblings():
    """Hidden siblings are excluded from inferred related commands."""
    group = CommandGroup(name="grp", commands=[_CommandA, _HiddenCommand, _CommandC])
    result = _infer_related(_CommandA, [group])
    assert result == ["gamma"]


def test_infer_related_excludes_self():
    """The command itself is not included in its own inferred related list."""
    group = CommandGroup(name="grp", commands=[_CommandA, _CommandB])
    result = _infer_related(_CommandA, [group])
    assert _CommandA.name not in result


def test_infer_related_no_siblings_returns_empty():
    """A command alone in its group returns empty list."""
    group = CommandGroup(name="grp", commands=[_CommandA])
    result = _infer_related(_CommandA, [group])
    assert result == []


def test_infer_related_command_not_in_any_group_returns_empty():
    """A command that is in none of the provided groups returns empty list."""
    group = CommandGroup(name="grp", commands=[_CommandB, _CommandC])
    result = _infer_related(_CommandA, [group])
    assert result == []


def test_infer_related_explicit_empty_returns_empty():
    """Explicit related_commands=[] returns empty list (distinct from None inference)."""
    group = CommandGroup(name="grp", commands=[_EmptyRelatedCommand, _CommandA])
    result = _infer_related(_EmptyRelatedCommand, [group])
    assert result == []


# ---------------------------------------------------------------------------
# Helper commands for _build_template_context tests
# ---------------------------------------------------------------------------


class _FullCommand(BaseCommand):
    name = "gen-docs"
    help_msg = "Generate documentation"
    overview = "  Long description of gen-docs.  "
    examples = [("Generate docs for myapp", "myapp gen-docs")]
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _MinimalCommand(BaseCommand):
    name = "run"
    help_msg = "Run the application"
    overview = ""
    examples = []
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _EmptyNameCommand(BaseCommand):
    name = ""
    help_msg = "A command"
    overview = ""
    examples = []
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


class _EmptyHelpCommand(BaseCommand):
    name = "ok"
    help_msg = ""
    overview = ""
    examples = []
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


# --- Tests for _build_template_context


def test_build_template_context_has_all_keys():
    """Returned dict contains exactly the 10 required keys."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    expected_keys = {
        "ref", "command_name", "short", "long", "synopsis",
        "examples", "flags", "related_commands", "heading_len", "appname",
    }
    assert set(result.keys()) == expected_keys


def test_build_template_context_command_name():
    """command_name matches the command class name attribute."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    assert result["command_name"] == _FullCommand.name


def test_build_template_context_short():
    """short matches the command's help_msg."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    assert result["short"] == _FullCommand.help_msg


def test_build_template_context_long_stripped():
    """long is the stripped overview."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    assert result["long"] == "Long description of gen-docs."


def test_build_template_context_long_empty():
    """long is empty string when overview is empty."""
    group = CommandGroup(name="grp", commands=[_MinimalCommand])
    result = _build_template_context(_MinimalCommand, "myapp", [group])
    assert result["long"] == ""


def test_build_template_context_synopsis_no_prefix():
    """synopsis has the 'usage: ' prefix stripped."""
    group = CommandGroup(name="grp", commands=[_MinimalCommand])
    result = _build_template_context(_MinimalCommand, "myapp", [group])
    assert not result["synopsis"].startswith("usage:")
    assert "myapp run" in result["synopsis"]


def test_build_template_context_examples_converted():
    """examples tuples are converted to ExampleInfo objects."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    assert result["examples"] == [
        ExampleInfo(info="Generate docs for myapp", usage="myapp gen-docs")
    ]


def test_build_template_context_flags_populated():
    """flags contains FlagInfo entries for the command's optional flags."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    flag_names = [f.name for f in result["flags"]]
    assert "--verbose" in flag_names


def test_build_template_context_related_commands():
    """related_commands is populated from _infer_related."""
    group = CommandGroup(name="grp", commands=[_FullCommand, _MinimalCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    assert result["related_commands"] == ["run"]


def test_build_template_context_heading_len():
    """heading_len equals len(command_name)."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    assert result["heading_len"] == len(_FullCommand.name)


def test_build_template_context_ref_hyphen_to_underscore():
    """ref replaces hyphens and spaces in command name with underscores."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "myapp", [group])
    assert result["ref"] == "gen_docs"


def test_build_template_context_appname():
    """appname passed through to the returned dict."""
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = _build_template_context(_FullCommand, "testapp", [group])
    assert result["appname"] == "testapp"


def test_build_template_context_empty_name_raises():
    """Empty command name raises ValueError."""
    group = CommandGroup(name="grp", commands=[_EmptyNameCommand])
    with pytest.raises(ValueError, match="command_name must not be empty"):
        _build_template_context(_EmptyNameCommand, "myapp", [group])


def test_build_template_context_empty_help_raises():
    """Empty help_msg raises ValueError."""
    group = CommandGroup(name="grp", commands=[_EmptyHelpCommand])
    with pytest.raises(ValueError, match="short.*must not be empty"):
        _build_template_context(_EmptyHelpCommand, "myapp", [group])


# ---------------------------------------------------------------------------
# Tests for gen_docs()
# ---------------------------------------------------------------------------


def test_gen_docs_renders_command_name():
    """gen_docs renders the command name into the writer via Jinja2 template."""
    writer = io.StringIO()
    group = CommandGroup(name="grp", commands=[_FullCommand])
    gen_docs(_FullCommand, writer, "{{ command_name }}", "myapp", [group])
    assert writer.getvalue() == "gen-docs"


def test_gen_docs_renders_flags():
    """gen_docs renders flag names into the writer via Jinja2 template."""
    writer = io.StringIO()
    group = CommandGroup(name="grp", commands=[_FullCommand])
    gen_docs(
        _FullCommand,
        writer,
        "{% for f in flags %}{{ f.name }}\n{% endfor %}",
        "myapp",
        [group],
    )
    assert "--verbose" in writer.getvalue()


def test_gen_docs_renders_short_description():
    """gen_docs renders the short description (help_msg) into the writer."""
    writer = io.StringIO()
    group = CommandGroup(name="grp", commands=[_FullCommand])
    gen_docs(_FullCommand, writer, "{{ short }}", "myapp", [group])
    assert writer.getvalue() == _FullCommand.help_msg


def test_gen_docs_returns_none():
    """gen_docs returns None (write-only side effect)."""
    writer = io.StringIO()
    group = CommandGroup(name="grp", commands=[_FullCommand])
    result = gen_docs(_FullCommand, writer, "{{ command_name }}", "myapp", [group])
    assert result is None


def test_gen_docs_does_not_flush_writer():
    """gen_docs does not flush the writer — the caller controls flushing."""

    class _TrackingStringIO(io.StringIO):
        def __init__(self) -> None:
            super().__init__()
            self.flushed = False

        def flush(self) -> None:
            self.flushed = True
            super().flush()

    writer = _TrackingStringIO()
    group = CommandGroup(name="grp", commands=[_FullCommand])
    gen_docs(_FullCommand, writer, "{{ command_name }}", "myapp", [group])
    assert writer.flushed is False


def test_gen_docs_rest_template():
    """gen_docs renders a reST-style template with heading underline correctly."""
    writer = io.StringIO()
    group = CommandGroup(name="grp", commands=[_FullCommand])
    template = "{{ command_name }}\n{{ command_name | length | repeat('=') }}\n\n{{ short }}"
    gen_docs(_FullCommand, writer, template, "myapp", [group])
    output = writer.getvalue()
    assert "gen-docs" in output
    assert "=" * len("gen-docs") in output
    assert _FullCommand.help_msg in output


# ---------------------------------------------------------------------------
# Helper command class with a multi-word name for gen_docs_tree tests
# ---------------------------------------------------------------------------


class _RemoteAddCommand(BaseCommand):
    name = "remote add"
    help_msg = "Add a remote"
    overview = "Remote add overview."
    related_commands = None

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, parsed_args: argparse.Namespace) -> None:
        pass


# ---------------------------------------------------------------------------
# Tests for gen_docs_tree()
# ---------------------------------------------------------------------------


def test_gen_docs_tree_creates_command_files(tmp_path):
    """gen_docs_tree writes one file per non-hidden command into output_dir."""
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template="{{ appname }}",
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_CommandA, _CommandB])
    gen_docs_tree("myapp", [group], tmp_path, templates)
    assert (tmp_path / "alpha.md").exists()
    assert (tmp_path / "beta.md").exists()
    assert (tmp_path / "alpha.md").read_text(encoding="utf-8") == "alpha"
    assert (tmp_path / "beta.md").read_text(encoding="utf-8") == "beta"


def test_gen_docs_tree_creates_index_file(tmp_path):
    """gen_docs_tree writes an index file using the index template."""
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template="{{ appname }}",
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_CommandA, _CommandB])
    gen_docs_tree("myapp", [group], tmp_path, templates)
    assert (tmp_path / "index.md").exists()
    assert "myapp" in (tmp_path / "index.md").read_text(encoding="utf-8")


def test_gen_docs_tree_index_receives_files_context(tmp_path):
    """Index template receives a files context with per-command metadata."""
    index_template = (
        "{% for f in files %}"
        "{{ f.filename }}:{{ f.command_name }}:{{ f.short }}:{{ f.group_name }}\n"
        "{% endfor %}"
    )
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template=index_template,
        index_file_name="index.md",
    )
    group = CommandGroup(name="mygroup", commands=[_CommandA, _CommandB])
    gen_docs_tree("myapp", [group], tmp_path, templates)
    content = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "alpha.md:alpha:Alpha command:mygroup" in content
    assert "beta.md:beta:Beta command:mygroup" in content


def test_gen_docs_tree_excludes_hidden_commands(tmp_path):
    """Hidden commands are absent from output files and index."""
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template=(
            "{% for f in files %}{{ f.filename }}\n{% endfor %}"
        ),
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_CommandA, _HiddenCommand])
    gen_docs_tree("myapp", [group], tmp_path, templates)
    assert not (tmp_path / "hidden-cmd.md").exists()
    index_content = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "hidden-cmd" not in index_content


def test_gen_docs_tree_returns_command_filenames_only(tmp_path):
    """gen_docs_tree returns list[str] of command filenames (index excluded)."""
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template="{{ appname }}",
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_CommandA, _CommandB])
    result = gen_docs_tree("myapp", [group], tmp_path, templates)
    assert result == ["alpha.md", "beta.md"]
    assert "index.md" not in result


def test_gen_docs_tree_creates_output_dir(tmp_path):
    """gen_docs_tree creates output_dir if it does not exist."""
    nested = tmp_path / "nested" / "docs"
    assert not nested.exists()
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template="{{ appname }}",
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_CommandA])
    gen_docs_tree("myapp", [group], nested, templates)
    assert nested.exists()
    assert (nested / "alpha.md").exists()


def test_gen_docs_tree_file_prepender_on_command_files(tmp_path):
    """file_prepender return value is prepended to command files."""
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template="{{ appname }}",
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_CommandA, _CommandB])
    gen_docs_tree(
        "myapp",
        [group],
        tmp_path,
        templates,
        file_prepender=lambda fn: f"<!-- {fn} -->\n",
    )
    alpha_content = (tmp_path / "alpha.md").read_text(encoding="utf-8")
    assert alpha_content.startswith("<!-- alpha.md -->\n")
    beta_content = (tmp_path / "beta.md").read_text(encoding="utf-8")
    assert beta_content.startswith("<!-- beta.md -->\n")


def test_gen_docs_tree_file_prepender_on_index_file(tmp_path):
    """file_prepender return value is prepended to the index file."""
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template="{{ appname }}",
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_CommandA])
    gen_docs_tree(
        "myapp",
        [group],
        tmp_path,
        templates,
        file_prepender=lambda fn: f"<!-- {fn} -->\n",
    )
    index_content = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert index_content.startswith("<!-- index.md -->\n")


def test_gen_docs_tree_custom_file_extension(tmp_path):
    """gen_docs_tree uses configurable file_extension for command files."""
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template="{{ appname }}",
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_CommandA, _CommandB])
    gen_docs_tree("myapp", [group], tmp_path, templates, file_extension=".rst")
    assert (tmp_path / "alpha.rst").exists()
    assert (tmp_path / "beta.rst").exists()
    assert not (tmp_path / "alpha.md").exists()


def test_gen_docs_tree_hyphenated_filenames(tmp_path):
    """Command names with spaces produce hyphenated filenames."""
    templates = TemplateInfo(
        command_template="{{ command_name }}",
        index_template="{{ appname }}",
        index_file_name="index.md",
    )
    group = CommandGroup(name="grp", commands=[_RemoteAddCommand])
    result = gen_docs_tree("myapp", [group], tmp_path, templates)
    assert "remote-add.md" in result
    assert (tmp_path / "remote-add.md").exists()


# ---------------------------------------------------------------------------
# Importability test (EXP-01)
# ---------------------------------------------------------------------------


def test_public_symbols_importable():
    """All five public gendocs symbols are importable from craft_cli (EXP-01)."""
    assert callable(craft_cli.gen_docs)
    assert callable(craft_cli.gen_docs_tree)
    # Dataclasses are also callable (constructors)
    assert callable(craft_cli.ExampleInfo)
    assert callable(craft_cli.FlagInfo)
    assert callable(craft_cli.TemplateInfo)
