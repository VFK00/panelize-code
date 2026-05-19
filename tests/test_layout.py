"""Tests for grid layout dimensions."""

from __future__ import annotations

import pytest

from panelize_code.layout import grid_dimensions


@pytest.mark.parametrize(
    "n,expected",
    [
        (0, (1, 1)),
        (1, (1, 1)),
        (2, (2, 1)),
        (3, (3, 1)),
        (4, (2, 2)),
        (5, (3, 2)),
        (6, (3, 2)),
        (7, (3, 3)),
        (9, (3, 3)),
        (10, (4, 3)),
        (12, (4, 3)),
        (13, (4, 4)),
        (16, (4, 4)),
    ],
)
def test_grid_dimensions(n: int, expected: tuple[int, int]) -> None:
    assert grid_dimensions(n) == expected
