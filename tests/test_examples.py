"""All example artifacts under examples/ must validate against their profile schema."""

from __future__ import annotations

import pytest

from validator.validate_examples import ROOT, validate_example

EXAMPLES = sorted((ROOT / "examples").glob("*/*.json"))


def test_examples_found() -> None:
    assert EXAMPLES, "expected at least one example artifact under examples/"


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: str(p.relative_to(ROOT)))
def test_example_validates(example) -> None:
    validate_example(example)
