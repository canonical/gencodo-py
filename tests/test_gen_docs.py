# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for gen_docs."""

import io

from gencodo import gen_docs
from tests.conftest import GreetCommand, HelloCommand


def test_gen_docs_writes_to_writer(command_groups):
    writer = io.StringIO()
    template = "# {{ command_name }}\n{{ short }}\n"
    gen_docs(GreetCommand, writer, template, "democli", command_groups)
    output = writer.getvalue()
    assert "# greet" in output
    assert "Greet a specific person" in output


def test_gen_docs_does_not_flush(command_groups):
    writer = io.StringIO()
    template = "{{ command_name }}"
    gen_docs(GreetCommand, writer, template, "democli", command_groups)
    # StringIO.flush is a no-op, but verify the writer position
    assert writer.tell() > 0


def test_gen_docs_renders_flags(command_groups):
    writer = io.StringIO()
    template = "{% for flag in flags %}{{ flag.name }}\n{% endfor %}"
    gen_docs(GreetCommand, writer, template, "democli", command_groups)
    output = writer.getvalue()
    assert "--formal" in output
    assert "--enthusiasm" in output


def test_gen_docs_renders_examples(command_groups):
    writer = io.StringIO()
    template = "{% for ex in examples %}{{ ex.info }}: {{ ex.usage }}\n{% endfor %}"
    gen_docs(GreetCommand, writer, template, "democli", command_groups)
    output = writer.getvalue()
    assert "Greet Alice" in output


def test_gen_docs_renders_related(command_groups):
    writer = io.StringIO()
    template = "{% for cmd in related_commands %}{{ cmd }}\n{% endfor %}"
    gen_docs(GreetCommand, writer, template, "democli", command_groups)
    output = writer.getvalue()
    assert "hello" in output
    assert "farewell" in output


def test_gen_docs_no_flags(command_groups):
    writer = io.StringIO()
    template = "flags: {{ flags | length }}"
    gen_docs(HelloCommand, writer, template, "democli", command_groups)
    assert writer.getvalue() == "flags: 0"


def test_gen_docs_extra_filters(command_groups):
    buf = io.StringIO()
    gen_docs(
        GreetCommand,
        buf,
        "{{ command_name | shout }}",
        "democli",
        command_groups,
        extra_filters={"shout": lambda s: s.upper()},
    )
    assert buf.getvalue() == "GREET"
