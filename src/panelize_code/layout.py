"""Auto grid layout: pick rows x cols based on panel count."""

from __future__ import annotations


def grid_dimensions(n_panels: int) -> tuple[int, int]:
    """Return (cols, rows) for n panels.

    Examples:
        1  -> (1, 1)
        2  -> (2, 1)
        3  -> (3, 1)
        4  -> (2, 2)
        5-6 -> (3, 2)
        7-9 -> (3, 3)
        10-12 -> (4, 3)
        else -> (4, ceil(n/4))
    """
    if n_panels <= 0:
        return (1, 1)
    if n_panels == 1:
        return (1, 1)
    if n_panels == 2:
        return (2, 1)
    if n_panels == 3:
        return (3, 1)
    if n_panels == 4:
        return (2, 2)
    if n_panels <= 6:
        return (3, 2)
    if n_panels <= 9:
        return (3, 3)
    if n_panels <= 12:
        return (4, 3)
    cols = 4
    rows = (n_panels + cols - 1) // cols
    return (cols, rows)
