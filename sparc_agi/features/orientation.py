from dataclasses import dataclass

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.range import Range

# Dihedral ops for d // 2 (same order as the input-rendering PoC), plus optional +45° when d % 2.
_TRANSFORMS = (
    lambda x, y: (x, y),
    lambda x, y: (-y, x),
    lambda x, y: (-x, -y),
    lambda x, y: (y, -x),
    lambda x, y: (x, -y),
    lambda x, y: (y, x),
    lambda x, y: (-x, y),
    lambda x, y: (-y, -x),
)

# Natural language for object / rotate descriptions (exact dirs 0–15).
_GEOMETRIC: dict[int, str] = {
    0: "",
    1: "rotated 45° counterclockwise",
    2: "rotated 90° counterclockwise",
    3: "rotated 135° counterclockwise",
    4: "rotated 180°",
    5: "rotated 135° clockwise",
    6: "rotated 90° clockwise",
    7: "rotated 45° clockwise",
    8: "flipped vertically",
    9: "flipped vertically and rotated 45° counterclockwise",
    10: "transposed",
    11: "transposed and rotated 45° counterclockwise",
    12: "flipped horizontally",
    13: "flipped horizontally and rotated 45° counterclockwise",
    14: "flipped over the anti-diagonal",
    15: "flipped over the anti-diagonal and rotated 45° counterclockwise",
}


def transform_xy(x: int, y: int, d: int) -> tuple[int, int]:
    """Apply the axis-aligned dihedral half of orientation ``d`` (45° dropped)."""
    even = d - (d % 2)
    return _TRANSFORMS[even // 2](x, y)


def scan_cells(width: int, height: int, d: int) -> list[tuple[int, int]]:
    """Cell coordinates in fill order for a ``width``×``height`` grid under ``d``.

    Identity fill is row-major; ``d``'s even dihedral half reorders/positions
    cells. The +45° bit is dropped by design for grids.
    """
    pts = [transform_xy(x, y, d) for y in range(height) for x in range(width)]
    min_x = min(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    return [(x - min_x, y - min_y) for x, y in pts]


def _grid_scan_phrase(d: int) -> str | None:
    """How identity row-major fill appears after orientation ``d``.

    Returns e.g. ``\"column by column from top to bottom and right to left\"``,
    or ``None`` for the default identity scan (omit from descriptions).
    """
    even = d - (d % 2)  # silently drop 45°
    if even == 0:
        return None

    n = 3
    pts = scan_cells(n, n, even)
    dx = pts[1][0] - pts[0][0]
    dy = pts[1][1] - pts[0][1]
    if dx != 0 and dy == 0:
        major = "row by row"
        along = "left to right" if dx > 0 else "right to left"
        across = "top to bottom" if pts[n][1] > pts[0][1] else "bottom to top"
    elif dy != 0 and dx == 0:
        major = "column by column"
        along = "top to bottom" if dy > 0 else "bottom to top"
        across = "left to right" if pts[n][0] > pts[0][0] else "right to left"
    else:
        return _GEOMETRIC.get(even) or f"orientation {even}"

    return f"{major} from {along} and {across}"


@register_feature("orientation", scalar=True)
@dataclass
class Orientation(Feature):
    value: Range

    def applied_to(self, previous: Orientation) -> Orientation:
        """Compose this orientation onto ``previous`` (additive on range bounds)."""
        base, delta = previous.value, self.value
        return Orientation(value=Range(base.lo + delta.lo, base.hi + delta.hi, base.step))

    def describe(self) -> str:
        """Geometric phrase for objects (e.g. ``flipped horizontally``)."""
        if self.value.lo != self.value.hi:
            return f"orientation {self.value.describe()}"
        return _GEOMETRIC.get(self.value.lo, f"orientation {self.value.lo}")

    def action_sentence(self, target: str) -> str:
        """Imperative step text applying this orientation to ``target``."""
        phrase = self.describe()
        if not phrase or phrase.startswith("orientation "):
            detail = phrase or self.value.describe()
            return f"Orient {target} with {detail}."
        verb, rest, _ = _action_parts(phrase)
        if rest:
            return f"{verb} {target} {rest}."
        return f"{verb} {target}."

    def result_alias(self, kind_noun: str, step: int) -> str:
        """Referential name for an object produced by applying this orientation."""
        phrase = self.describe()
        if not phrase or phrase.startswith("orientation "):
            return f"oriented {kind_noun} from step {step}"
        _, _, stem = _action_parts(phrase)
        return f"{stem} {kind_noun} from step {step}"

    def grid_scan_phrase(self) -> str | None:
        """Scan-order phrase for grids (45° ignored), or ``None`` when default."""
        if self.value.lo != self.value.hi:
            return f"orientation {self.value.describe()}"
        return _grid_scan_phrase(self.value.lo)


def _action_parts(phrase: str) -> tuple[str, str, str]:
    """Map a geometric phrase to ``(Verb, remainder after target, alias stem)``."""
    if phrase.startswith("flipped "):
        rest = phrase.removeprefix("flipped ").replace(" and rotated ", " and rotate ")
        return "Flip", rest, "flipped"
    if phrase.startswith("rotated "):
        return "Rotate", phrase.removeprefix("rotated "), "rotated"
    if phrase == "transposed":
        return "Transpose", "", "transposed"
    if phrase.startswith("transposed "):
        rest = phrase.removeprefix("transposed ").replace(" and rotated ", " and rotate ")
        return "Transpose", rest, "transposed"
    return "Orient", phrase, "oriented"
