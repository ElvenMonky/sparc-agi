from dataclasses import dataclass
from sparc_agi.features.base import FeatureSpec

@dataclass
class MappingSpec(FeatureSpec):
    key: str = ""
    variants: int | None = None
