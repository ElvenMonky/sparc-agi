"""ARC color palettes.

Puzzle specs constrain a palette with logical-to-display color assignments.
At generation time a :class:`Palette` completes those constraints to a
permutation of the ten ARC colors.
"""

import random
from dataclasses import dataclass, field

from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

COLOR_NAMES = (
    "black",
    "blue",
    "red",
    "green",
    "yellow",
    "grey",
    "magenta",
    "orange",
    "teal",
    "maroon",
)

COLOR_HEX = (
    "#000000",
    "#0074D9",
    "#FF4136",
    "#2ECC40",
    "#FFDC00",
    "#AAAAAA",
    "#F012BE",
    "#FF851B",
    "#7FDBFF",
    "#870C25",
)

COLOR_COUNT = len(COLOR_NAMES)

@dataclass(frozen=True)
class PaletteSpec:
    fixed: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        values: set[int] = set()
        for key, value in self.fixed.items():
            if not isinstance(key, int) or not 0 <= key < COLOR_COUNT:
                raise ValueError(f"palette key must be an integer in 0..{COLOR_COUNT - 1}, got {key!r}")
            if not isinstance(value, int) or not 0 <= value < COLOR_COUNT:
                raise ValueError(f"palette value must be an integer in 0..{COLOR_COUNT - 1}, got {value!r}")
            if value in values:
                raise ValueError(f"palette colors must be unique, got {dict(self.fixed)!r}")
            values.add(value)

    def instantiate(self, rng: random.Random) -> Palette:
        free_values = [color for color in range(COLOR_COUNT) if color not in self.fixed.values()]
        rng.shuffle(free_values)
        values = tuple(self.fixed[key] if key in self.fixed else free_values.pop() for key in range(COLOR_COUNT))
        return Palette(values)

@dataclass(frozen=True)
class Palette:
    colors: tuple[int, int, int, int, int, int, int, int, int, int]

    def __post_init__(self) -> None:
        self.validate()

    @classmethod
    def identity(cls) -> Palette:
        return cls(tuple(range(COLOR_COUNT)))

    def validate(self) -> None:
        if len(self.colors) != COLOR_COUNT:
            raise ValueError(f"palette must contain {COLOR_COUNT} colors, got {len(self.colors)}")
        if min(self.colors) != 0 or max(self.colors) != COLOR_COUNT - 1:
            raise ValueError(f"palette colors must be in 0..{COLOR_COUNT - 1}, got {self.colors!r}")
        if len(set(self.colors)) != COLOR_COUNT:
            raise ValueError(f"palette must be a permutation, got {self.colors!r}")

    def color_name(self, key: int) -> str:
        return COLOR_NAMES[self.colors[key]]

    def color_phrase(self, key: int) -> str:
        value = self.colors[key]
        return f"{COLOR_NAMES[value]} ({value})"

    def plot(self, ax: Axes, *, title: str = "Palette") -> None:
        ax.clear()
        for key, value in enumerate(self.colors):
            ax.add_patch(
                Rectangle(
                    (key, 0),
                    1,
                    1,
                    facecolor=COLOR_HEX[value],
                    edgecolor="#666666",
                    linewidth=0.5,
                )
            )
            text_color = "white" if value in (0, 1, 6, 9) else "black"
            ax.text(
                key + 0.5,
                0.5,
                f"{value}",
                ha="center",
                va="center",
                color=text_color,
                fontsize=8,
            )
        ax.set(xlim=(0, COLOR_COUNT), ylim=(0, 1), aspect="equal", title=title)
        ax.axis("off")
