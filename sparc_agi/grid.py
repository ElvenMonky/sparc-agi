"""Grid helpers for object instantiation and transformation."""

from __future__ import annotations

from sparc_agi.features.orientation import transform_xy

Grid = list[list[int]]
Placement = tuple[tuple[int, int], int]


def grid_size(grid: Grid) -> tuple[int, int]:
    if not grid:
        return (0, 0)
    return (len(grid[0]), len(grid))


def apply_orientation(grid: Grid, direction: int) -> Grid:
    """Map each cell through ``direction``'s axis-aligned dihedral transform."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    pts = [
        (*transform_xy(x, y, direction), grid[y][x])
        for y in range(height)
        for x in range(width)
    ]
    min_x = min(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    pts = [(x - min_x, y - min_y, v) for x, y, v in pts]
    out_w = max(p[0] for p in pts) + 1
    out_h = max(p[1] for p in pts) + 1
    out: Grid = [[-1] * out_w for _ in range(out_h)]
    for x, y, v in pts:
        out[y][x] = v
    return out


def to_arc_grid(grid: Grid) -> Grid:
    """Replace transparent (``-1``) cells with ARC background ``0``."""
    return [[0 if cell < 0 else cell for cell in row] for row in grid]


def compose_placements(
    placements: list[Placement],
    pool: list[Grid],
    *,
    width: int | None = None,
    height: int | None = None,
    gap: int = 0,
    margin: int = 0,
) -> Grid:
    """Stamp pool grids onto arrangement slots.

    ``placements`` entries are ``((grid_x, grid_y), pool_index)``. Empty /
    missing slots stay transparent (``-1``); callers can convert with
    ``to_arc_grid`` for ARC JSON output.
    """
    if not pool:
        raise ValueError("compose_placements requires a non-empty pool")
    cell_w = max(grid_size(g)[0] for g in pool)
    cell_h = max(grid_size(g)[1] for g in pool)
    if cell_w == 0 or cell_h == 0:
        raise ValueError("pool items must be non-empty grids")

    if width is None:
        width = max((x for (x, _), _ in placements), default=-1) + 1
    if height is None:
        height = max((y for (_, y), _ in placements), default=-1) + 1
    if width <= 0 or height <= 0:
        return []

    stride_x = cell_w + gap
    stride_y = cell_h + gap
    out_w = margin * 2 + width * cell_w + max(0, width - 1) * gap
    out_h = margin * 2 + height * cell_h + max(0, height - 1) * gap
    out: Grid = [[-1] * out_w for _ in range(out_h)]

    filled = {(x, y): idx for (x, y), idx in placements}
    for gy in range(height):
        for gx in range(width):
            idx = filled.get((gx, gy))
            if idx is None or idx < 0 or idx >= len(pool):
                continue
            stamp = pool[idx]
            sw, sh = grid_size(stamp)
            ox = margin + gx * stride_x
            oy = margin + gy * stride_y
            for y in range(sh):
                for x in range(sw):
                    val = stamp[y][x]
                    if val < 0:
                        continue
                    out[oy + y][ox + x] = val
    return out
