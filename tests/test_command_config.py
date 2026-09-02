# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for the command_config parameter."""

from __future__ import annotations

import argparse
import io

import pytest

from gencodo import CommandGroup, TemplateInfo, gen_docs, gen_docs_tree


class ConfigRequiredCommand:
    """A command whose __init__ requires a non-None config dict."""

    name = "cfg-cmd"
    help_msg = "Needs config"
    overview = "This command requires a config dict."
    hidden = False
    examples = [("Run it", "app cfg-cmd")]
    related_commands = None

    def __init__(self, config):
        if config is None:
            raise TypeError("config must not be None")
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        default_name = self.config.get("default_name", "world")
        parser.add_argument("--name", default=default_name, help="Name to use")


@pytest.fixture
def cfg_groups():
    return [CommandGroup(name="Config", commands=[ConfigRequiredCommand])]


@pytest.fixture
def cfg_config():
    return {"default_name": "gencodo"}


class TestGenDocsWithConfig:
    def test_gen_docs_with_command_config(self, cfg_groups, cfg_config):
        writer = io.StringIO()
        template = "# {{ command_name }}\n{% for f in flags %}{{ f.name }}={{ f.default_value }}\n{% endfor %}"
        gen_docs(
            ConfigRequiredCommand,
            writer,
            template,
            "app",
            cfg_groups,
            command_config=cfg_config,
        )
        output = writer.getvalue()
        assert "# cfg-cmd" in output
        assert "--name=gencodo" in output

    def test_gen_docs_without_config_uses_default_behaviour(self, cfg_groups):
        """Existing callers that don't pass command_config still work."""
        from tests.conftest import GreetCommand

        groups = [CommandGroup(name="G", commands=[GreetCommand])]
        writer = io.StringIO()
        template = "{{ command_name }}"
        gen_docs(GreetCommand, writer, template, "app", groups)
        assert writer.getvalue() == "greet"


class TestGenDocsTreeWithConfig:
    def test_gen_docs_tree_with_command_config(self, tmp_path, cfg_groups, cfg_config):
        templates = TemplateInfo(
            index_file_name="index.md",
            index_template="# Index\n{% for f in files %}{{ f.command_name }}\n{% endfor %}",
            command_template="# {{ command_name }}\n{% for f in flags %}{{ f.name }}={{ f.default_value }}\n{% endfor %}",
        )
        generated = gen_docs_tree(
            "app",
            cfg_groups,
            tmp_path,
            templates,
            command_config=cfg_config,
        )
        assert "cfg-cmd.md" in generated
        content = (tmp_path / "cfg-cmd.md").read_text(encoding="utf-8")
        assert "--name=gencodo" in content

    def test_gen_docs_tree_without_config_unchanged(self, tmp_path, command_groups):
        """Existing callers without command_config still work."""
        templates = TemplateInfo(
            index_file_name="index.md",
            index_template="idx",
            command_template="{{ command_name }}",
        )
        generated = gen_docs_tree("app", command_groups, tmp_path, templates)
        assert "greet.md" in generated


class TestInstantiateCommandWithConfig:
    def test_config_required_without_config_raises(self):
        """ConfigRequiredCommand cannot be instantiated with None."""
        with pytest.raises(TypeError):
            ConfigRequiredCommand(None)

    def test_config_required_with_config_succeeds(self, cfg_config):
        cmd = ConfigRequiredCommand(cfg_config)
        assert cmd.config == cfg_config
