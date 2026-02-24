"""Tests for _make_jinja_env."""

import pytest
from jinja2 import StrictUndefined, UndefinedError

from gencodo._jinja_env import _make_jinja_env


def test_env_has_strict_undefined():
    env = _make_jinja_env()
    assert env.undefined is StrictUndefined


def test_env_no_autoescape():
    env = _make_jinja_env()
    assert env.autoescape is False


def test_env_trim_blocks():
    env = _make_jinja_env()
    assert env.trim_blocks is True


def test_env_lstrip_blocks():
    env = _make_jinja_env()
    assert env.lstrip_blocks is True


def test_env_keep_trailing_newline():
    env = _make_jinja_env()
    assert env.keep_trailing_newline is True


def test_indent_filter():
    env = _make_jinja_env()
    tmpl = env.from_string("{{ text | indent(4) }}")
    result = tmpl.render(text="hello\nworld")
    assert result == "    hello\n    world"


def test_indent_filter_first_line():
    env = _make_jinja_env()
    tmpl = env.from_string("{{ text | indent(2) }}")
    result = tmpl.render(text="hello")
    assert result == "  hello"


def test_repeat_filter():
    env = _make_jinja_env()
    tmpl = env.from_string("{{ '=' | repeat(5) }}")
    result = tmpl.render()
    assert result == "====="


def test_repeat_filter_zero():
    env = _make_jinja_env()
    tmpl = env.from_string("{{ '-' | repeat(0) }}")
    result = tmpl.render()
    assert result == ""


def test_strict_undefined_raises():
    env = _make_jinja_env()
    tmpl = env.from_string("{{ missing_var }}")
    with pytest.raises(UndefinedError):
        tmpl.render()
