from dataclasses import dataclass, field
from typing import Any

from sparc_agi.range import Range

@dataclass(frozen=True)
class Cut:
    tl: Range = field(default_factory=lambda: Range(0))
    tr: Range = field(default_factory=lambda: Range(0))
    br: Range = field(default_factory=lambda: Range(0))
    bl: Range = field(default_factory=lambda: Range(0))

    @classmethod
    def from_raw(cls, raw: Any) -> Cut:
        if isinstance(raw, Cut):
            return raw
        if isinstance(raw, (int, list, Range)):
            value = Range.from_raw(raw)
            return cls(value, value, value, value)
        if isinstance(raw, dict):
            unknown = set(raw) - {"tl", "tr", "br", "bl"}
            if unknown:
                raise ValueError(f"cut object has unknown keys {unknown}")
            return cls(
                tl=Range.from_raw(raw.get("tl", 0)),
                tr=Range.from_raw(raw.get("tr", 0)),
                br=Range.from_raw(raw.get("br", 0)),
                bl=Range.from_raw(raw.get("bl", 0)),
            )
        raise ValueError(f"cut must be a range or corner object, got {raw!r}")

    def to_raw(self) -> int | list[int] | dict[str, int | list[int]]:
        values = (
            self.tl,
            self.tr,
            self.br,
            self.bl,
        )
        if all(value == values[0] for value in values[1:]):
            return values[0].to_raw()
        return {
            name: value.to_raw()
            for name, value in (
                ("tl", self.tl),
                ("tr", self.tr),
                ("br", self.br),
                ("bl", self.bl),
            )
            if value != Range(0)
        }
