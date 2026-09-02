# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""Tests for positional-argument and flag extraction."""

from __future__ import annotations

import argparse

from gencodo._core import _build_parser, _build_template_context, _extract_arguments


class RichCommand:
    name = "rich"
    help_msg = "Exercise every argparse feature gencodo documents"
    overview = "Overview."
    hidden = False
    examples: list[tuple[str, str]] = []
    related_commands = None

    def __init__(self, config=None):
        self.config = config

    def fill_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("sdk", metavar="SDK", help="Name of the SDK")
        parser.add_argument("parts", nargs="*", help="Parts to build")
        parser.add_argument("mode", choices=["fast", "slow"], default="fast", help="Mode")
        parser.add_argument("-o", "--output", metavar="PATH", default=".", help="Output path")
        parser.add_argument("--policy", choices=("strict", "permissive"), help="Policy")
        parser.add_argument("--track", action="append", dest="tracks", required=True, help="Track")
        parser.add_argument("-v", "--verbose", action="store_true", help="Talk more")
        parser.add_argument("-q", action="count", default=0, help="Quieter")
        parser.add_argument("--secret", help=argparse.SUPPRESS)
        parser.add_argument("nope", help=argparse.SUPPRESS)


def _extract():
    return _extract_arguments(_build_parser(RichCommand, "app rich"))


def test_positional_arguments_in_order():
    arguments, _ = _extract()
    assert [a.name for a in arguments] == ["SDK", "parts", "mode"]
    sdk, parts, mode = arguments
    assert sdk.usage == "Name of the SDK"
    assert sdk.metavar == "SDK"
    assert sdk.nargs == ""
    assert parts.nargs == "*"
    assert parts.metavar == ""
    assert mode.choices == ("fast", "slow")
    assert mode.default_value == "fast"


def test_suppressed_actions_are_excluded():
    arguments, flags = _extract()
    assert all(a.name != "nope" for a in arguments)
    assert all(f.name != "--secret" for f in flags)


def test_flag_short_and_long_options():
    _, flags = _extract()
    by_name = {f.name: f for f in flags}
    output = by_name["--output"]
    assert output.short == "-o"
    assert output.option_strings == ("-o", "--output")
    assert output.metavar == "PATH"
    assert output.default_value == "."
    assert not output.is_flag
    assert not output.required


def test_flag_without_short_option():
    _, flags = _extract()
    policy = {f.name: f for f in flags}["--policy"]
    assert policy.short == ""
    assert policy.option_strings == ("--policy",)
    assert policy.choices == ("strict", "permissive")


def test_required_append_flag():
    _, flags = _extract()
    track = {f.name: f for f in flags}["--track"]
    assert track.required
    assert track.metavar == ""


def test_value_less_flags_have_no_default_or_metavar():
    _, flags = _extract()
    by_name = {f.name: f for f in flags}
    verbose = by_name["--verbose"]
    assert verbose.is_flag
    assert verbose.short == "-v"
    assert verbose.default_value == ""
    assert verbose.metavar == ""
    quiet = by_name["-q"]
    assert quiet.is_flag
    assert quiet.short == ""
    assert quiet.default_value == ""


def test_synopsis_is_a_single_line(command_groups):
    ctx = _build_template_context(RichCommand, "app", command_groups)
    assert "\n" not in ctx["synopsis"]
    assert ctx["synopsis"].startswith("app rich ")
    assert "SDK" in ctx["synopsis"]


def test_context_exposes_arguments_and_file_name(command_groups):
    ctx = _build_template_context(
        RichCommand, "app", command_groups, file_prefix="app-", file_extension=".rst"
    )
    assert [a.name for a in ctx["arguments"]] == ["SDK", "parts", "mode"]
    assert ctx["filename"] == "app-rich.rst"
    assert ctx["group_name"] == ""
    assert ctx["hidden"] is False
    assert ctx["common"] is False
