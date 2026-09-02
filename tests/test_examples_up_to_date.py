# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

"""The committed demo output must match what the library generates."""

from __future__ import annotations

import pathlib
import runpy

import pytest

EXAMPLE_DIR = pathlib.Path(__file__).resolve().parent.parent / "examples" / "demo_cli"


@pytest.fixture
def generated(tmp_path: pathlib.Path) -> pathlib.Path:
    """Run examples/demo_cli/generate_docs.py into a temporary directory."""
    runpy.run_path(
        str(EXAMPLE_DIR / "generate_docs.py"),
        init_globals={"OUTPUT_DIR_OVERRIDE": tmp_path},
        run_name="__main__",
    )
    return tmp_path


def test_committed_docs_output_is_current(generated: pathlib.Path):
    committed = EXAMPLE_DIR / "docs_output"
    expected = sorted(p.relative_to(committed) for p in committed.rglob("*") if p.is_file())
    actual = sorted(p.relative_to(generated) for p in generated.rglob("*") if p.is_file())
    assert actual == expected, "run `make examples` and commit the result"
    for rel in expected:
        assert (generated / rel).read_text() == (committed / rel).read_text(), (
            f"{rel} is stale: run `make examples` and commit the result"
        )
