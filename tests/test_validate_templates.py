# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for validate_templates()."""

from __future__ import annotations

import jinja2
import pytest

from gencodo import TemplateInfo, get_bundled_templates, validate_templates


def _templates(command: str = "{{ command_name }}", index: str = "{{ appname }}") -> TemplateInfo:
    return TemplateInfo(
        index_file_name="index.rst", index_template=index, command_template=command
    )


def test_bundled_templates_validate():
    validate_templates(get_bundled_templates("rst"))
    validate_templates(get_bundled_templates("md"))


def test_every_context_key_is_available():
    command = (
        "{{ ref }}{{ command_name }}{{ short }}{{ long }}{{ synopsis }}{{ heading_len }}"
        "{{ appname }}{{ hidden }}{{ common }}{{ group_name }}{{ filename }}"
        "{% for e in examples %}{{ e.info }}{{ e.usage }}{% endfor %}"
        "{% for a in arguments %}{{ a.name }}{{ a.usage }}{{ a.nargs }}{{ a.choices }}{% endfor %}"
        "{% for f in flags %}{{ f.short }}{{ f.name }}{{ f.metavar }}{{ f.required }}{{ f.is_flag }}{% endfor %}"
        "{% for c in related_commands %}{{ c }}{% endfor %}"
    )
    index = "{% for f in files %}{{ f.filename }}{{ f.ref }}{{ f.group_name }}{% endfor %}{{ commands | length }}"
    validate_templates(_templates(command, index))


def test_unknown_command_variable_fails():
    with pytest.raises(jinja2.UndefinedError):
        validate_templates(_templates(command="{{ nope }}"))


def test_unknown_index_variable_fails():
    with pytest.raises(jinja2.UndefinedError):
        validate_templates(_templates(index="{{ nope }}"))


def test_unknown_filter_fails():
    with pytest.raises(jinja2.TemplateAssertionError):
        validate_templates(_templates(command="{{ short | nosuch }}"))


def test_else_branch_is_exercised():
    with pytest.raises(jinja2.UndefinedError):
        validate_templates(_templates(command="{% if flags %}ok{% else %}{{ nope }}{% endif %}"))


def test_extra_filters_are_honoured():
    validate_templates(
        _templates(command="{{ short | shout }}"),
        extra_filters={"shout": lambda s: s + "!"},
    )
