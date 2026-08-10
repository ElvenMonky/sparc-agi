from dataclasses import dataclass
from typing import Any, Self, get_args, get_origin

@dataclass(frozen=True)
class Sequence[Min: int, Max: int]:
    prefix: tuple[int, ...] = ()
    pattern: tuple[int, ...] = ()

    @classmethod
    def bounds(cls, typ: type) -> tuple[int, int] | None:
        origin = get_origin(typ) or typ
        if origin is Sequence:
            args = get_args(typ)
            if len(args) == 2 and all(isinstance(arg, int) for arg in args):
                return args[0], args[1]
        return None

    @classmethod
    def _validate_items(cls, items: tuple[int, ...], bounds: tuple[int, int] | None) -> None:
        if bounds is None:
            return
        lo, hi = bounds
        for item in items:
            if item < lo or item > hi:
                raise ValueError(f"sequence item {item} is outside {lo}..{hi}")

    @classmethod
    def structure(cls, value: Any, typ: type) -> Self:
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise ValueError(f"sequence must be an object, got {value!r}")
        prefix = value.get("prefix", [])
        pattern = value.get("pattern", [])
        if not isinstance(prefix, list) or not isinstance(pattern, list):
            raise ValueError(f"sequence prefix and pattern must be lists, got {value!r}")
        items = prefix + pattern
        if not all(isinstance(item, int) and not isinstance(item, bool) for item in items):
            raise ValueError(f"sequence items must be integers, got {value!r}")
        bounds = cls.bounds(typ)
        prefix_t = tuple(prefix)
        pattern_t = tuple(pattern)
        cls._validate_items(prefix_t, bounds)
        cls._validate_items(pattern_t, bounds)
        return cls(prefix_t, pattern_t)

    def unstructure(self) -> dict[str, list[int]]:
        payload: dict[str, list[int]] = {}
        if self.prefix:
            payload["prefix"] = list(self.prefix)
        if self.pattern:
            payload["pattern"] = list(self.pattern)
        return payload
