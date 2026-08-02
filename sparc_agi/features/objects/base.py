"""Base class for ``object.*`` feature kinds."""

import random
from dataclasses import dataclass

from sparc_agi.geometry import Geometry
from sparc_agi.features.base import FeatureSpec, Feature

@dataclass
class ObjectSpec(FeatureSpec):
    pass

@dataclass
class Object(Feature):
    spec: ObjectSpec
