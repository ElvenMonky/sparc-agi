"""Footprint composite: the area an arrangement occupies."""

from dataclasses import dataclass

from sparc_agi.features.size import Size


@dataclass
class Footprint:
    size: Size

    def describe(self) -> str:
        return f"footprint {self.size.describe()}"
