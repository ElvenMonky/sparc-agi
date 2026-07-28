"""Grid helpers for object instantiation and transformation."""

from sparc_agi.features.scalars.orientation import transform_xy

Grid = list[list[int]]
Placement = tuple[tuple[int, int], int]
BBox = tuple[int, int, int, int]  # x, y, w, h


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


def placements_to_mask(placements: list[Placement]) -> Grid:
    """Binary occupancy grid covering placement coordinates."""
    if not placements:
        return []
    width = max(x for (x, _), _ in placements) + 1
    height = max(y for (_, y), _ in placements) + 1
    out: Grid = [[0] * width for _ in range(height)]
    for (x, y), _ in placements:
        out[y][x] = 1
    return out


def _stamp_clipped(out: Grid, stamp: Grid, ox: int, oy: int) -> None:
    """Stamp ``stamp`` onto ``out`` at ``(ox, oy)``, clipping to canvas bounds."""
    out_h = len(out)
    out_w = len(out[0]) if out else 0
    sw, sh = grid_size(stamp)
    for y in range(sh):
        py = oy + y
        if py < 0 or py >= out_h:
            continue
        for x in range(sw):
            px = ox + x
            if px < 0 or px >= out_w:
                continue
            val = stamp[y][x]
            if val < 0:
                continue
            out[py][px] = val


def bboxes_respect_gap(a: BBox, b: BBox, gap_x: int, gap_y: int) -> bool:
    """True if boxes keep at least ``gap_x`` / ``gap_y`` between edges.

    Gaps may be negative to allow overlap of up to ``-gap`` pixels on that axis.
    """
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (
        ax + aw + gap_x <= bx
        or bx + bw + gap_x <= ax
        or ay + ah + gap_y <= by
        or by + bh + gap_y <= ay
    )


def compose_placements(
    placements: list[Placement],
    pool: list[Grid],
    *,
    width: int | None = None,
    height: int | None = None,
    gap_x: int = 0,
    gap_y: int = 0,
    margin_left: int = 0,
    margin_right: int = 0,
    margin_top: int = 0,
    margin_bottom: int = 0,
) -> Grid:
    """Stamp pool grids onto a virtual-cell arrangement.

    ``placements`` entries are ``((cell_x, cell_y), pool_index)``. Cell size is
    the max pool item size; gaps / margins are in pixels (may be negative).
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

    stride_x = cell_w + gap_x
    stride_y = cell_h + gap_y
    content_w = (width - 1) * stride_x + cell_w
    content_h = (height - 1) * stride_y + cell_h
    out_w = content_w + margin_left + margin_right
    out_h = content_h + margin_top + margin_bottom
    if out_w <= 0 or out_h <= 0:
        return []

    out: Grid = [[-1] * out_w for _ in range(out_h)]
    filled = {(x, y): idx for (x, y), idx in placements}
    for gy in range(height):
        for gx in range(width):
            idx = filled.get((gx, gy))
            if idx is None or idx < 0 or idx >= len(pool):
                continue
            stamp = pool[idx]
            ox = margin_left + gx * stride_x
            oy = margin_top + gy * stride_y
            _stamp_clipped(out, stamp, ox, oy)
    return out


def compose_free(
    width: int,
    height: int,
    items: list[tuple[tuple[int, int], Grid]],
) -> Grid:
    """Stamp items at absolute pixel top-lefts onto a fixed-size object grid."""
    if width <= 0 or height <= 0:
        return []
    out: Grid = [[-1] * width for _ in range(height)]
    for (ox, oy), stamp in items:
        _stamp_clipped(out, stamp, ox, oy)
    return out
