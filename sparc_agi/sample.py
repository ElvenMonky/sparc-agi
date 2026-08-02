from dataclasses import dataclass, field
from sparc_agi.range import RangeSpec

@dataclass
class SampleSpec:
    train: RangeSpec = field(default_factory=lambda: RangeSpec(2, 5))
    test: RangeSpec = field(default_factory=lambda: RangeSpec(1, 3))