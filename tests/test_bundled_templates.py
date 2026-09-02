# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for get_bundled_templates and bundled template rendering."""

import io

import pytest

from gencodo import TemplateInfo, gen_docs, gen_docs_tree, get_bundled_templates
from tests.conftest import GreetCommand


def test_get_bundled_templates_rst():
    ti = get_bundled_templates("rst")
    assert isinstance(ti, TemplateInfo)
    assert ti.index_file_name == "index.rst"
    assert "{{ command_name }}" in ti.command_template
    assert "{{ appname }}" in ti.index_template


def test_get_bundled_templates_md():
    ti = get_bundled_templates("md")
    assert isinstance(ti, TemplateInfo)
    assert ti.index_file_name == "index.md"
    assert "{{ command_name }}" in ti.command_template
    assert "{{ appname }}" in ti.index_template


def test_get_bundled_templates_custom_index_name():
    ti = get_bundled_templates("rst", index_file_name="custom-index.rst")
    assert ti.index_file_name == "custom-index.rst"


def test_get_bundled_templates_invalid_format():
    with pytest.raises(ValueError, match="format must be"):
        get_bundled_templates("html")  # type: ignore[arg-type]


def test_bundled_rst_renders(command_groups):
    ti = get_bundled_templates("rst")
    writer = io.StringIO()
    gen_docs(GreetCommand, writer, ti.command_template, "democli", command_groups)
    output = writer.getvalue()
    assert ".. _ref_greet:" in output
    assert "greet" in output
    assert "=====" in output
    assert "democli greet" in output
    assert ".. option:: --formal" in output
    assert "**Greet Alice**" in output


def test_bundled_md_renders(command_groups):
    ti = get_bundled_templates("md")
    writer = io.StringIO()
    gen_docs(GreetCommand, writer, ti.command_template, "democli", command_groups)
    output = writer.getvalue()
    assert "# greet" in output
    assert "democli greet" in output
    assert "`--formal`" in output
    assert "**Greet Alice**" in output


def test_bundled_rst_tree(tmp_path, command_groups):
    ti = get_bundled_templates("rst")
    generated = gen_docs_tree("democli", command_groups, tmp_path, ti, file_extension=".rst")
    assert "greet.rst" in generated
    assert (tmp_path / "index.rst").exists()

    content = (tmp_path / "greet.rst").read_text(encoding="utf-8")
    assert ".. _ref_greet:" in content


def test_bundled_md_tree(tmp_path, command_groups):
    ti = get_bundled_templates("md")
    generated = gen_docs_tree("democli", command_groups, tmp_path, ti)
    assert "greet.md" in generated
    assert (tmp_path / "index.md").exists()

    content = (tmp_path / "greet.md").read_text(encoding="utf-8")
    assert "# greet" in content


def test_bundled_rst_index_renders(command_groups, tmp_path):
    ti = get_bundled_templates("rst")
    gen_docs_tree("democli", command_groups, tmp_path, ti, file_extension=".rst")
    idx = (tmp_path / "index.rst").read_text(encoding="utf-8")
    assert "CLI Reference" in idx
    assert "democli" in idx
    assert ".. toctree::" in idx


def test_bundled_md_index_renders(command_groups, tmp_path):
    ti = get_bundled_templates("md")
    gen_docs_tree("democli", command_groups, tmp_path, ti)
    idx = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "# CLI Reference" in idx
    assert "democli" in idx
