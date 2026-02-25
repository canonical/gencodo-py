"""Unit tests for gencodo dataclasses and types."""

import dataclasses

import pytest

from gencodo import Command, CommandClass, CommandGroup, ExampleInfo, FlagInfo, TemplateInfo


# --- Tests for FlagInfo ---


def test_flag_info_construction():
    fi = FlagInfo(name="--verbose", usage="Enable verbose output", default_value="false")
    assert fi.name == "--verbose"
    assert fi.usage == "Enable verbose output"
    assert fi.default_value == "false"


# --- Tests for ExampleInfo ---


def test_example_info_construction():
    ei = ExampleInfo(info="Build the project", usage="myapp build")
    assert ei.info == "Build the project"
    assert ei.usage == "myapp build"


# --- Tests for TemplateInfo ---


def test_template_info_valid_construction():
    ti = TemplateInfo(
        index_file_name="index.md",
        index_template="# Index\n",
        command_template="# {{ command_name }}\n",
    )
    assert ti.index_file_name == "index.md"


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
    with pytest.raises(ValueError, match=f"TemplateInfo.{bad_field} must not be empty"):
        TemplateInfo(
            index_file_name=index_file_name,
            index_template=index_template,
            command_template=command_template,
        )


def test_template_info_whitespace_only_raises():
    with pytest.raises(ValueError, match="TemplateInfo.index_template must not be empty"):
        TemplateInfo(index_file_name="file", index_template="   ", command_template="cmd")


# --- Tests for frozen/hashable behavior ---


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
    field_name = dataclasses.fields(instance)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, field_name, "new_value")


def test_dataclasses_support_equality():
    assert FlagInfo("a", "b", "c") == FlagInfo("a", "b", "c")
    assert ExampleInfo("info", "usage") == ExampleInfo("info", "usage")
    assert TemplateInfo("idx.md", "# Index", "# Cmd") == TemplateInfo(
        "idx.md", "# Index", "# Cmd"
    )


# --- Tests for Command Protocol ---


def test_command_protocol_satisfied(command_groups):
    """Helper command classes satisfy the Command protocol."""
    for group in command_groups:
        for cmd_class in group.commands:
            assert isinstance(cmd_class, type)
            # Check base protocol attributes exist on class
            assert hasattr(cmd_class, "name")
            assert hasattr(cmd_class, "help_msg")
            assert hasattr(cmd_class, "hidden")


def test_command_class_is_type_alias():
    """CommandClass is a type alias for type[Command]."""

    class ValidClass:
        name = "valid"
        help_msg = "Valid command"
        hidden = False

    # CommandClass is type[Command]; instances of ValidClass satisfy Command
    assert isinstance(ValidClass(), Command)
    assert isinstance(ValidClass, type)


def test_command_protocol_is_runtime_checkable():
    """Command protocol supports isinstance checks on instances."""

    class ValidInstance:
        name = "valid"
        help_msg = "Valid command"
        hidden = False

    assert isinstance(ValidInstance(), Command)


def test_extension_attributes_not_in_command_protocol():
    """Command protocol does not require overview, examples, or related_commands."""

    class MinimalCommand:
        name = "minimal"
        help_msg = "Minimal"
        hidden = False

    # Should satisfy Command without extension attributes
    assert isinstance(MinimalCommand(), Command)


# --- Tests for CommandGroup ---


def test_command_group_is_named_tuple():
    from gencodo import CommandGroup

    cg = CommandGroup(name="Test", commands=[])
    assert cg.name == "Test"
    assert cg.commands == []
    assert cg[0] == "Test"
    assert cg[1] == []
