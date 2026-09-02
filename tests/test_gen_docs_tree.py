# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for gen_docs_tree."""

import jinja2
import pytest

from gencodo import TemplateInfo, gen_docs_tree


@pytest.fixture
def simple_templates():
    return TemplateInfo(
        index_file_name="index.md",
        index_template="# Index\n{% for f in files %}{{ f.command_name }}\n{% endfor %}",
        command_template="# {{ command_name }}\n{{ short }}\n",
    )


def test_gen_docs_tree_creates_output_dir(tmp_path, command_groups, simple_templates):
    out = tmp_path / "docs" / "ref"
    gen_docs_tree("democli", command_groups, out, simple_templates)
    assert out.is_dir()


def test_gen_docs_tree_returns_command_filenames(tmp_path, command_groups, simple_templates):
    generated = gen_docs_tree("democli", command_groups, tmp_path, simple_templates)
    assert "greet.md" in generated
    assert "hello.md" in generated
    assert "farewell.md" in generated
    # index is NOT in the returned list
    assert "index.md" not in generated


def test_gen_docs_tree_skips_hidden(tmp_path, command_groups, simple_templates):
    generated = gen_docs_tree("democli", command_groups, tmp_path, simple_templates)
    assert "secret.md" not in generated
    assert not (tmp_path / "secret.md").exists()


def test_gen_docs_tree_creates_files(tmp_path, command_groups, simple_templates):
    gen_docs_tree("democli", command_groups, tmp_path, simple_templates)
    assert (tmp_path / "greet.md").exists()
    assert (tmp_path / "hello.md").exists()
    assert (tmp_path / "index.md").exists()


def test_gen_docs_tree_file_content(tmp_path, command_groups, simple_templates):
    gen_docs_tree("democli", command_groups, tmp_path, simple_templates)
    content = (tmp_path / "greet.md").read_text(encoding="utf-8")
    assert "# greet" in content
    assert "Greet a specific person" in content


def test_gen_docs_tree_index_content(tmp_path, command_groups, simple_templates):
    gen_docs_tree("democli", command_groups, tmp_path, simple_templates)
    content = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "# Index" in content
    assert "greet" in content


def test_gen_docs_tree_file_prepender(tmp_path, command_groups, simple_templates):
    def prepender(filename: str) -> str:
        return f"<!-- {filename} -->\n"

    gen_docs_tree("democli", command_groups, tmp_path, simple_templates, file_prepender=prepender)
    content = (tmp_path / "greet.md").read_text(encoding="utf-8")
    assert content.startswith("<!-- greet.md -->")

    idx = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert idx.startswith("<!-- index.md -->")


def test_gen_docs_tree_custom_extension(tmp_path, command_groups, simple_templates):
    generated = gen_docs_tree(
        "democli", command_groups, tmp_path, simple_templates, file_extension=".rst"
    )
    assert "greet.rst" in generated
    assert (tmp_path / "greet.rst").exists()


def test_gen_docs_tree_space_in_command_name(tmp_path):
    """Command names with spaces become hyphenated filenames."""

    class SpaceCommand:
        name = "multi word"
        help_msg = "Multi-word command"
        overview = ""
        hidden = False
        examples = []
        related_commands = None

        def __init__(self, config=None):
            pass

        def fill_parser(self, parser):
            pass

    from gencodo import CommandGroup

    groups = [CommandGroup(name="Test", commands=[SpaceCommand])]
    templates = TemplateInfo(
        index_file_name="index.md",
        index_template="idx",
        command_template="{{ command_name }}",
    )
    generated = gen_docs_tree("app", groups, tmp_path, templates)
    assert "multi-word.md" in generated
    assert (tmp_path / "multi-word.md").exists()


def test_gen_docs_tree_file_prefix(tmp_path, command_groups):
    templates = TemplateInfo(
        index_file_name="app.rst",
        index_template="{% for f in files %}{{ f.filename }} {% endfor %}",
        command_template="{{ filename }}",
    )
    generated = gen_docs_tree(
        appname="democli",
        command_groups=command_groups,
        output_dir=tmp_path,
        templates=templates,
        file_extension=".rst",
        file_prefix="app-",
    )
    expected = [f"app-{c.name}.rst" for g in command_groups for c in g.commands if not c.hidden]
    assert generated == expected
    assert (tmp_path / "app-greet.rst").read_text() == "app-greet.rst"
    assert (tmp_path / "app.rst").read_text().split() == generated


def test_gen_docs_tree_dry_run(tmp_path, command_groups):
    out = tmp_path / "out"
    templates = TemplateInfo(index_file_name="index.md", index_template="i", command_template="c")
    generated = gen_docs_tree(
        appname="democli",
        command_groups=command_groups,
        output_dir=out,
        templates=templates,
        dry_run=True,
    )
    assert generated == [
        f"{c.name}.md" for g in command_groups for c in g.commands if not c.hidden
    ]
    assert not out.exists()


def test_gen_docs_tree_template_error_writes_nothing(tmp_path, command_groups):
    out = tmp_path / "out"
    templates = TemplateInfo(
        index_file_name="index.md", index_template="i", command_template="{{ nope }}"
    )
    with pytest.raises(jinja2.UndefinedError):
        gen_docs_tree(
            appname="democli", command_groups=command_groups, output_dir=out, templates=templates
        )
    assert not out.exists()


def test_gen_docs_tree_extra_filters(tmp_path, command_groups):
    templates = TemplateInfo(
        index_file_name="index.md",
        index_template="{{ appname | shout }}",
        command_template="{{ command_name | shout }}",
    )
    gen_docs_tree(
        appname="democli",
        command_groups=command_groups,
        output_dir=tmp_path,
        templates=templates,
        extra_filters={"shout": lambda s: s.upper() + "!"},
    )
    assert (tmp_path / "greet.md").read_text() == "GREET!"
    assert (tmp_path / "index.md").read_text() == "DEMOCLI!"


def test_gen_docs_tree_index_gets_commands_and_ref(tmp_path, command_groups):
    templates = TemplateInfo(
        index_file_name="index.md",
        index_template="{% for c in commands %}{{ c.ref }}:{{ c.group_name }} {% endfor %}",
        command_template="c",
    )
    gen_docs_tree(
        appname="democli", command_groups=command_groups, output_dir=tmp_path, templates=templates
    )
    assert (tmp_path / "index.md").read_text().split() == [
        f"{c.name.replace('-', '_')}:{g.name}"
        for g in command_groups
        for c in g.commands
        if not c.hidden
    ]
