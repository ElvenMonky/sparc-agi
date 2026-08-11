import random
from dataclasses import dataclass
from typing import Any, Self, get_args, get_origin

@dataclass(frozen=True)
class Range[Min: int, Max: int]:
    lo: int = 0
    hi: int | None = None
    step: int = 1

    def __post_init__(self) -> None:
        if self.hi is None:
            object.__setattr__(self, "hi", self.lo)

    @classmethod
    def bounds(cls, typ: type) -> tuple[int, int] | None:
        origin = get_origin(typ) or typ
        if origin is Range:
            args = get_args(typ)
            if len(args) == 2 and all(isinstance(arg, int) for arg in args):
                return args[0], args[1]
        return None

    @classmethod
    def _validate(cls, lo: int, hi: int, bounds: tuple[int, int] | None) -> None:
        if lo > hi:
            raise ValueError(f"range lower bound {lo} exceeds upper bound {hi}")
        if bounds is None:
            return
        lo_min, lo_max = bounds
        if lo < lo_min or lo > lo_max or hi < lo_min or hi > lo_max:
            raise ValueError(f"range [{lo}, {hi}] is outside {lo_min}..{lo_max}")

    @classmethod
    def structure(cls, value: Any, typ: type) -> Self:
        if isinstance(value, cls):
            return value
        if isinstance(value, bool) or not isinstance(value, (int, list)):
            raise ValueError(f"range must be an integer or list, got {value!r}")
        bounds = cls.bounds(typ)
        if isinstance(value, int):
            cls._validate(value, value, bounds)
            return cls(value)
        if not 1 <= len(value) <= 3 or not all(isinstance(item, int) for item in value):
            raise ValueError(f"range list must contain 1 to 3 integers, got {value!r}")
        lo = value[0]
        hi = value[1] if len(value) > 1 else lo
        step = value[2] if len(value) > 2 else 1
        if step < 1:
            raise ValueError(f"range step must be positive, got {step}")
        cls._validate(lo, hi, bounds)
        return cls(lo, hi, step)

    def unstructure(self) -> int | list[int]:
        if self.lo == self.hi and self.step == 1:
            return self.lo
        if self.step == 1:
            return [self.lo, self.hi]
        return [self.lo, self.hi, self.step]

    def instantiate(self, rng: random.Random) -> int:
        return rng.randrange(self.lo, self.hi + 1, self.step)

    def is_fixed(self) -> bool:
        return self.lo == self.hi

    def describe(self) -> str:
        if self.is_fixed():
            return str(self.lo)
        if self.step == 1:
            return f"{self.lo}-{self.hi}"
        if self.step == 2:
            parity = "even" if self.lo % 2 == 0 else "odd"
            return f"{self.lo}-{self.hi} ({parity})"
        n_max = (self.hi - self.lo) // self.step
        return f"{self.step}xN+{self.lo} (N=0..{n_max})"
