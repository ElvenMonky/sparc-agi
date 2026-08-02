from dataclasses import dataclass, field
from sparc_agi.range import Range
from sparc_agi.features.base import Feature
from sparc_agi.features.object import Object

@dataclass
class SampleSpec:
    train: Range = field(default_factory=lambda: Range(2, 5))
    test: Range = field(default_factory=lambda: Range(1, 3))

@dataclass
class Sample:
    spec: SampleSpec
    input: Object = field(default_factory=Object)
    steps: list[Feature] = field(default_factory=list)