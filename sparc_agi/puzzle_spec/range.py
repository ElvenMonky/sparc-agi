import random
from dataclasses import dataclass
from typing import Any, Self

@dataclass(frozen=True)
class Range:
    lo: int = 0
    hi: int | None = None
    step: int = 1

    def __post_init__(self) -> None:
        if self.hi is None:
            object.__setattr__(self, "hi", self.lo)

    @classmethod
    def structure(cls, value: Any, _: type) -> Self:
        if isinstance(value, bool) or not isinstance(value, (int, list)):
            raise ValueError(f"range must be an integer or list, got {value!r}")
        if isinstance(value, int):
            return cls(value)
        if not 1 <= len(value) <= 3 or not all(isinstance(item, int) for item in value):
            raise ValueError(f"range list must contain 1 to 3 integers, got {value!r}")
        lo = value[0]
        hi = value[1] if len(value) > 1 else lo
        step = value[2] if len(value) > 2 else 1
        if step < 1:
            raise ValueError(f"range step must be positive, got {step}")
        return cls(lo, hi, step)

    def unstructure(self) -> int | list[int]:
        if self.lo == self.hi and self.step == 1:
            return self.lo
        if self.step == 1:
            return [self.lo, self.hi]
        return [self.lo, self.hi, self.step]

    def instantiate(self, rng: random.Random) -> int:
        return rng.randrange(self.lo, self.hi + 1, self.step)
