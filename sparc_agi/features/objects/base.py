from dataclasses import dataclass
from sparc_agi.features.base import FeatureSpec, Feature
from sparc_agi.features.origin import Origin

@dataclass
class ObjectSpec(FeatureSpec):
    origin: Origin | None = None
    mapping: str | None = None

@dataclass
class PoolItem:
    object: ObjectSpec
    variants: int | None = None

@dataclass
class Object(Feature):
    spec: ObjectSpec
