"""Tests for gen_docs_tree."""

import pathlib

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


def test_gen_docs_tree_returns_command_filenames(
    tmp_path, command_groups, simple_templates
):
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

    gen_docs_tree(
        "democli", command_groups, tmp_path, simple_templates, file_prepender=prepender
    )
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
