# Agentic Prompt: Fix type checking for `gencodo.CommandGroup.commands` (#4)

## Context

This task addresses a type-safety concern raised by @jonathan-conder in
canonical/sdkcraft PR#209. The fix spans two repositories:

1. **`gencodo-py`** (upstream library) — structural typing changes
2. **`sdkcraft`** (consumer) — remove the `cast()` workaround

---

## Background

In `sdkcraft/commands/gendocs.py`, `GenerateDocsCommand.run()` builds a list of
`gencodo.CommandGroup` objects by iterating over `self._command_groups` (which
are `craft_cli.CommandGroup` objects). The `commands` field of each group holds
a sequence of `craft_cli.BaseCommand` subclasses, but `gencodo.CommandGroup`
expects `Sequence[type[Command]]` for its own `Command` type.

Currently the mismatch is papered over with a bare `cast()`:

```python
# sdkcraft/commands/gendocs.py ~line 71
CommandGroup(
    name=g.name,
    commands=cast("Sequence[type[Command]]", g.commands),
)
```

Jonathan's review comment:
> "Something is off with the type checking here. I suggest making
> `gencodo.CommandGroup.commands` a `Sequence[CommandClass]`, where
> `CommandClass` is a `Protocol` with a `__call__` method that returns a
> `Command` (another `Protocol`). Anything that isn't defined in
> `craft_cli.BaseCommand` should not be in the `Protocol`, use `getattr`
> instead."

---

## Step 1 — Changes in `gencodo-py`

### Locate the relevant types

Find `gencodo-py`'s source (likely on GitHub at
`canonical/gencodo` or similar). Identify:
- The current type of `CommandGroup.commands`
- The current `Command` type (concrete class vs. Protocol)
- The `gen_docs_tree` function signature, specifically how it uses
  `command_groups`

### Define `CommandClass` Protocol

Add a `CommandClass` Protocol that captures **only** the interface
`gencodo` itself uses when constructing commands. At minimum this is
the constructor call, so:

```python
from typing import Protocol, runtime_checkable

class Command(Protocol):
    """Structural type for an instantiated command."""
    name: str
    help_msg: str
    hidden: bool
    # Add any other attributes gencodo actually reads off a Command instance.
    # Do NOT include attributes from craft_cli.BaseCommand that gencodo
    # never touches. For any optional/extra attributes, use getattr() inside
    # gencodo's rendering code rather than declaring them here.

class CommandClass(Protocol):
    """Structural type for a command class (factory)."""
    def __call__(self, config: dict | None = None) -> Command: ...
    # Also expose class-level attributes that gencodo reads before
    # instantiation (e.g. `name`, `hidden`) as Protocol members if needed.
```

Key rules per reviewer guidance:
- **Only attributes/methods that `craft_cli.BaseCommand` guarantees** belong
  in the Protocol.
- Anything that might only exist on some subclasses (e.g. `examples`,
  `related_commands`, `overview`) must be accessed via `getattr(cmd, "examples", [])` etc. inside `gencodo`'s template rendering/introspection code.

### Update `CommandGroup.commands`

Change the field type from whatever it currently is to:

```python
from collections.abc import Sequence

@dataclass  # or however CommandGroup is defined
class CommandGroup:
    name: str
    commands: Sequence[CommandClass]
```

### Audit `gencodo` internals for attribute access

Search every place in `gencodo` that accesses attributes on a command
class or instance. For each attribute:
- If it is defined on `craft_cli.BaseCommand` → keep direct access, add to Protocol.
- If it is an extension attribute (e.g. `examples`, `always_load_project`,
  `related_commands`) → replace with `getattr(cmd, "attr", default)`.

### Tests & release

- Update/add unit tests for the new Protocols in `gencodo-py`.
- Bump version (at minimum a patch release, semver-compatible).

---

## Step 2 — Changes in `sdkcraft`

Once the new `gencodo-py` version is available (or as a local editable
install for development), update `sdkcraft`:

### `sdkcraft/commands/gendocs.py`

1. **Remove the `cast()`** in `GenerateDocsCommand.run()`:

   Before:
   ```python
   CommandGroup(
       name=g.name,
       commands=cast("Sequence[type[Command]]", g.commands),
   )
   ```
   After:
   ```python
   CommandGroup(
       name=g.name,
       commands=g.commands,
   )
   ```

2. **Remove the now-unused `cast` import** from `typing` if nothing else
   uses it in this file.

3. **Remove the `Command` TYPE_CHECKING import** from `gencodo` if it is no
   longer needed directly (it may still be needed if used in type annotations
   elsewhere in the file — check carefully).

4. **Run the type checker** (`pyright` and/or `mypy`) to confirm no residual
   type errors:
   ```
   pyright sdkcraft/commands/gendocs.py
   mypy sdkcraft/commands/gendocs.py
   ```

### `pyproject.toml`

Pin the new `gencodo-py` version that includes the Protocol types:
```toml
"gencodo-py>=<new_version>",
```

---

## Acceptance criteria

- [ ] `gencodo-py` defines `Command` and `CommandClass` as structural Protocols.
- [ ] `gencodo.CommandGroup.commands` is typed as `Sequence[CommandClass]`.
- [ ] All internal attribute accesses in `gencodo` on command objects use
      `getattr()` for non-`BaseCommand` attributes.
- [ ] `sdkcraft/commands/gendocs.py` has **no `cast()` call** when building
      `CommandGroup` objects.
- [ ] `pyright` and `mypy` pass cleanly on `gendocs.py` with the updated
      `gencodo-py`.
- [ ] No functional regression: `sdkcraft generate-docs` still produces
      correct output.
