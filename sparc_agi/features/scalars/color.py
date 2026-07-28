"""ARC color indices, names, and per-puzzle palette remapping."""

import random
from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

from sparc_agi.features.base import Scalar, register_feature
from sparc_agi.grid import Grid

# Canonical ARC-AGI palette (logical index → name). Matches plotting swatches.
COLOR_NAMES: tuple[str, ...] = (
    "black",  # 0
    "blue",  # 1
    "red",  # 2
    "green",  # 3
    "yellow",  # 4
    "grey",  # 5
    "magenta",  # 6
    "orange",  # 7
    "teal",  # 8
    "maroon",  # 9
)

# Active display remap: palette[logical] = display index. None → identity.
_palette: ContextVar[tuple[int, ...] | None] = ContextVar("color_palette", default=None)


def color_name(index: int) -> str:
    """Canonical name for a display color index, or ``color N`` if out of range."""
    if 0 <= index < len(COLOR_NAMES):
        return COLOR_NAMES[index]
    return f"color {index}"


def color_phrase(logical: int) -> str:
    """Named color for a logical index, after the active palette remap if any.

    Example: ``black (0)``.
    """
    palette = _palette.get()
    display = palette[logical] if palette is not None and 0 <= logical < len(palette) else logical
    return f"{color_name(display)} ({display})"


def describe_color_values(values: Sequence[int]) -> str:
    """Join color phrases: ``blue (1)`` or ``blue (1), red (2), green (3)``."""
    return ", ".join(color_phrase(v) for v in values)


def random_palette(
    rng: random.Random,
    fixed: Mapping[int, int] | None = None,
) -> tuple[int, ...]:
    """Build a permutation ``display = palette[logical]`` for ``0..9``.

    ``fixed`` locks some logical→display pairs (e.g. ``{0: 0}`` keeps background
    black). Remaining logical colors are shuffled into the unused display slots.
    """
    fixed_map = {int(k): int(v) for k, v in (fixed or {}).items()}
    for logical, display in fixed_map.items():
        if not (0 <= logical <= 9 and 0 <= display <= 9):
            raise ValueError(
                f"palette fix {logical}→{display} must use indices in 0..9"
            )
    if len(set(fixed_map.values())) != len(fixed_map):
        raise ValueError(f"palette fixes must use unique display colors, got {fixed_map}")

    free_logical = [i for i in range(10) if i not in fixed_map]
    free_display = [i for i in range(10) if i not in fixed_map.values()]
    rng.shuffle(free_display)
    palette = [0] * 10
    for logical, display in fixed_map.items():
        palette[logical] = display
    for logical, display in zip(free_logical, free_display, strict=True):
        palette[logical] = display
    return tuple(palette)


def apply_palette(grid: Grid, palette: Sequence[int]) -> Grid:
    """Remap cell indices through ``palette`` (leaves out-of-range / negative alone)."""
    n = len(palette)
    return [[palette[c] if 0 <= c < n else c for c in row] for row in grid]


@contextmanager
def use_palette(palette: Sequence[int] | None) -> Iterator[None]:
    """Apply ``palette`` to :func:`color_phrase` for the duration of the block."""
    token = _palette.set(tuple(palette) if palette is not None else None)
    try:
        yield
    finally:
        _palette.reset(token)


@register_feature("color")
@dataclass
class Color(Scalar):
    def describe(self) -> str:
        assert self.value.hi is not None
        values = list(range(self.value.lo, self.value.hi + 1, self.value.step))
        return describe_color_values(values)
