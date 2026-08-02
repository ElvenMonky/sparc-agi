from dataclasses import dataclass, field, replace
from typing import Optional

Points = list[tuple[int, int]]
ColoredPoints = list[tuple[int, int, Optional[int]]]
Grid = list[list[int]]

def _point_in_polygon(px: int, py: int, vertices: Points) -> bool:
    inside = False
    for i in range(len(vertices)):
        x0, y0 = vertices[i]
        x1, y1 = vertices[i - 1]
        if (y0 > py) != (y1 > py):
            x_edge = x0 + (py - y0) * (x1 - x0) / (y1 - y0)
            if px < x_edge:
                inside = not inside
    return inside

def _rotate45(x: int, y: int) -> tuple[int, int]:
    flip = y < 0 or (y == 0 and x < 0)
    if flip:
        x, y = -x, -y
    m = ((1, 0), (1, 1))
    if y <= x:
        m = ((1, -1), (1, 0))
    elif x >= 0:
        m = ((1, -1), (0, 1))
    elif y >= -x:
        m = ((0, -1), (1, 1))
    rx = m[0][0] * x + m[0][1] * y
    ry = m[1][0] * x + m[1][1] * y
    return (-rx, -ry) if flip else (rx, ry)

@dataclass
class Geometry:
    """Instantiated object: local pose, optional fill, nested children."""

    x: int = 0
    y: int = 0
    dir: int = 0
    color: Optional[int] = None
    edge_color: Optional[int] = None
    vertice_color: Optional[int] = None
    vertices: Points = field(default_factory=list)
    geometries: list[Geometry] = field(default_factory=list)
    # Sized container (root free group, etc.); bounds for :meth:`to_grid`.
    width: int | None = None
    height: int | None = None
    # Pool index when this node was placed as a group child (for pick/remove).
    slot: int | None = None
    # Donor geometry this node was instantiated from (cache / prior instance).
    source: Geometry | None = None

    def copy(self) -> Geometry:
        """Deep copy of this subtree."""
        return replace(
            self,
            vertices=list(self.vertices),
            geometries=[g.copy() for g in self.geometries],
        )

    def transform(self, x: int, y: int, c: Optional[int]) -> tuple[int, int, Optional[int]]:
        d = self.dir
        x, y = [
            (x, y),
            (-y, x),
            (-x, -y),
            (y, -x),
            (x, -y),
            (y, x),
            (-x, y),
            (-y, -x),
        ][d // 2]
        if d % 2 == 1:
            x, y = _rotate45(x, y)
        return x + self.x, y + self.y, c

    def render_own_geometry(self, inherited_color: Optional[int] = None) -> ColoredPoints:
        color = self.color if self.color is not None else inherited_color
        if not self.vertices:
            return []
        # Single vertex → one ARC cell (point objects).
        if len(self.vertices) == 1:
            if color is None:
                return []
            vx, vy = self.vertices[0]
            return [(vx, vy, color)]

        points: dict[int, dict[int, Optional[int]]] = {}
        xs, ys = [v[0] for v in self.vertices], [v[1] for v in self.vertices]
        min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
        for py in range(min_y, max_y + 1):
            points[py] = {}
            for px in range(min_x, max_x + 1):
                if _point_in_polygon(px, py, self.vertices):
                    points[py][px] = color
        if self.edge_color is not None:
            color = self.edge_color
        for i in range(len(self.vertices)):
            x0, y0 = self.vertices[i]
            x1, y1 = self.vertices[i - 1]
            if x0 == x1:
                for y in range(min(y0, y1), max(y0, y1) + 1):
                    points.setdefault(y, {})[x0] = color
            elif y0 == y1:
                for x in range(min(x0, x1), max(x0, x1) + 1):
                    points.setdefault(y0, {})[x] = color
            elif abs(x1 - x0) == abs(y1 - y0):
                steps = abs(x1 - x0)
                sx = 1 if x1 > x0 else -1
                sy = 1 if y1 > y0 else -1
                for s in range(steps + 1):
                    points.setdefault(y0 + s * sy, {})[x0 + s * sx] = color
        if self.vertice_color is not None:
            color = self.vertice_color
        for vx, vy in self.vertices:
            points.setdefault(vy, {})[vx] = color
        return [(x, y, points[y][x]) for y in points for x in points[y]]

    def render(self, inherited_color: Optional[int] = None) -> ColoredPoints:
        color = self.color if self.color is not None else inherited_color
        points = self.render_own_geometry(inherited_color)
        for child in self.geometries:
            points.extend(child.render(color))
        return [self.transform(*p) for p in points]

    def bbox(self) -> tuple[int, int, int, int] | None:
        """Axis-aligned ``(x, y, w, h)`` of rendered positive cells, or ``None``."""
        pts = [(x, y) for x, y, c in self.render() if c is not None and c > 0]
        if not pts:
            return None
        min_x = min(x for x, _ in pts)
        min_y = min(y for _, y in pts)
        max_x = max(x for x, _ in pts)
        max_y = max(y for _, y in pts)
        return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

    def crop_to_content(self) -> Geometry:
        """Copy rebaked so occupied cells sit at ``(0, 0)`` with tight ``width``/``height``.

        Used by wrapper objects (tree, glyph, …) when no explicit size was given:
        grow/place freely, then shrink to the rendered footprint for placement.
        """
        box = self.bbox()
        if box is None:
            out = self.copy()
            out.x = 0
            out.y = 0
            out.width = 0
            out.height = 0
            return out
        ox, oy, w, h = box
        out = self.copy()
        out.x = 0
        out.y = 0
        out.width = w
        out.height = h
        out.vertices = [(vx - ox, vy - oy) for vx, vy in out.vertices]
        for child in out.geometries:
            child.x -= ox
            child.y -= oy
        return out

    def size(self) -> tuple[int, int]:
        """Pixel size: explicit container size, else tight bbox, else ``(0, 0)``."""
        if self.width is not None and self.height is not None:
            return (self.width, self.height)
        box = self.bbox()
        if box is None:
            return (0, 0)
        return (box[2], box[3])

    def to_grid(self, *, background: int = -1) -> Grid:
        """Rasterize into a flat grid (emit / plot boundary only)."""
        if self.width is not None and self.height is not None:
            w, h = self.width, self.height
            ox = oy = 0
            pts = self.render()
        else:
            box = self.bbox()
            if box is None:
                return []
            ox, oy, w, h = box
            pts = [(x - ox, y - oy, c) for x, y, c in self.render()]
        if w <= 0 or h <= 0:
            return []
        out: Grid = [[background] * w for _ in range(h)]
        for x, y, c in pts:
            if c is None or c < 0:
                continue
            if 0 <= x < w and 0 <= y < h:
                out[y][x] = c
        return out

    def apply_orientation(self, direction: int) -> Geometry:
        """Bake a dihedral transform into axis-aligned coords (top-left at origin).

        Setting only ``dir`` rotates around the local origin, so even-sized shapes
        get a bbox that no longer starts at ``(0, 0)``. Placement code assigns
        ``x``/``y`` as the stamp top-left and would then shift the content.
        Rebaking keeps size and origin stable under later placement.
        """
        if direction == 0:
            return self.copy()
        probe = self.copy()
        probe.dir = direction
        probe.x = 0
        probe.y = 0
        probe.width = None
        probe.height = None
        pts = [(x, y, c) for x, y, c in probe.render() if c is not None]
        if not pts:
            out = self.copy()
            out.dir = 0
            return out
        min_x = min(x for x, _, _ in pts)
        min_y = min(y for _, y, _ in pts)
        max_x = max(x for x, _, _ in pts)
        max_y = max(y for _, y, _ in pts)
        children = [
            point_geometry(c, x=x - min_x, y=y - min_y) for x, y, c in pts
        ]
        return Geometry(
            width=max_x - min_x + 1,
            height=max_y - min_y + 1,
            geometries=children,
            source=self.source,
            slot=self.slot,
        )

    def recolor(self, new_color: int) -> Geometry:
        """Deep copy with this node's color set; recurse into children that have color."""
        out = self.copy()
        if out.color is not None or not out.geometries:
            out.color = new_color
        out.geometries = [g.recolor(new_color) for g in out.geometries]
        return out

    def as_root(self) -> Geometry:
        """Copy as a standalone root: drop parent-relative ``x``/``y`` (and ``slot``)."""
        out = self.copy()
        out.x = 0
        out.y = 0
        out.slot = None
        return out

    def child_at(self, index: int) -> Geometry:
        """Direct child at ``index`` (raises if out of range)."""
        try:
            return self.geometries[index]
        except IndexError as exc:
            raise IndexError(
                f"geometry index {index} out of range (have {len(self.geometries)} children)"
            ) from exc

    def without_index(self, index: int) -> Geometry:
        """Copy with the direct child at ``index`` removed."""
        if index < 0 or index >= len(self.geometries):
            raise IndexError(
                f"geometry index {index} out of range (have {len(self.geometries)} children)"
            )
        out = self.copy()
        out.geometries = [g for i, g in enumerate(out.geometries) if i != index]
        return out

    def replace_index(self, index: int, new_child: Geometry) -> Geometry:
        """Copy replacing the direct child at ``index`` (pose of the old child kept)."""
        if index < 0 or index >= len(self.geometries):
            raise IndexError(
                f"geometry index {index} out of range (have {len(self.geometries)} children)"
            )
        out = self.copy()
        old = out.geometries[index]
        child = new_child.copy()
        child.x, child.y = old.x, old.y
        child.slot = old.slot
        out.geometries = list(out.geometries)
        out.geometries[index] = child
        return out

    def find_slot(self, slot: int) -> Geometry | None:
        for child in self.geometries:
            if child.slot == slot:
                return child
        return None

    def without_slot(self, slot: int) -> Geometry:
        """Copy with the direct child matching ``slot`` removed."""
        out = self.copy()
        out.geometries = [g for g in out.geometries if g.slot != slot]
        return out

    def replace_slot(self, slot: int, new_child: Geometry) -> Geometry:
        """Copy replacing the direct child with ``slot`` by ``new_child`` (pose preserved)."""
        out = self.copy()
        geoms: list[Geometry] = []
        replaced = False
        for g in out.geometries:
            if g.slot == slot:
                child = new_child.copy()
                child.x, child.y = g.x, g.y
                child.slot = slot
                geoms.append(child)
                replaced = True
            else:
                geoms.append(g)
        if not replaced:
            raise ValueError(f"no child with slot {slot}")
        out.geometries = geoms
        return out

def point_geometry(color: int, *, x: int = 0, y: int = 0, slot: int | None = None) -> Geometry:
    return Geometry(x=x, y=y, color=color, vertices=[(0, 0)], slot=slot)

def geometry_occupancy(geom: Geometry) -> tuple[tuple[int, ...], ...]:
    """Translation-normalized binary mask of positive cells (for arrangement→color maps)."""
    pts = [(x, y) for x, y, c in geom.render() if c is not None and c > 0]
    if not pts:
        return ()
    min_x = min(x for x, _ in pts)
    min_y = min(y for _, y in pts)
    max_x = max(x for x, _ in pts)
    max_y = max(y for _, y in pts)
    w, h = max_x - min_x + 1, max_y - min_y + 1
    mask = [[0] * w for _ in range(h)]
    for x, y in pts:
        mask[y - min_y][x - min_x] = 1
    return tuple(tuple(row) for row in mask)
