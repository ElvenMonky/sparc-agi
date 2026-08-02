import random
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Range:
    lo: int
    hi: int | None = None
    step: int = 1

    def __post_init__(self) -> None:
        if self.hi is None:
            object.__setattr__(self, "hi", self.lo)

    @classmethod
    def from_raw(cls, raw: Any) -> Range:
        if isinstance(raw, Range):
            return raw
        if isinstance(raw, bool) or not isinstance(raw, (int, list)):
            raise ValueError(f"range must be an int or list, got {raw!r}")
        if isinstance(raw, int):
            return cls(raw)
        if not (1 <= len(raw) <= 3):
            raise ValueError(f"range list must have 1..3 ints, got {raw!r}")
        lo = int(raw[0])
        hi = int(raw[1]) if len(raw) > 1 else lo
        step = int(raw[2]) if len(raw) > 2 else 1
        if step < 1:
            raise ValueError(f"range step must be >= 1, got {step}")
        return cls(lo, hi, step)

    def to_raw(self) -> int | list[int]:
        if self.lo == self.hi and self.step == 1:
            return self.lo
        if self.step == 1:
            return [self.lo, self.hi]
        return [self.lo, self.hi, self.step]

    def describe(self) -> str:
        if self.lo == self.hi and self.step == 1:
            return str(self.lo)
        if self.step == 1:
            return f"{self.lo}..{self.hi}"
        return f"{self.lo}..{self.hi} with step {self.step}"

    def sample(self, rng: random.Random) -> int:
        n = (self.hi - self.lo) // self.step + 1
        if n <= 0:
            raise ValueError(f"empty range {self.to_raw()!r}")
        return self.lo + rng.randrange(n) * self.step
