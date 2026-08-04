from dataclasses import dataclass, field

from sparc_agi.range import Range

@dataclass
class SampleSpec:
    train: Range = field(default_factory=lambda: Range(2, 5))
    test: Range = field(default_factory=lambda: Range(1, 3))
