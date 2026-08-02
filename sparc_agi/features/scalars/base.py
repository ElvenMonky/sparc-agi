import random
from dataclasses import dataclass

from sparc_agi.features.base import FeatureSpec
from sparc_agi.range import RangeSpec

@dataclass(frozen=True)
class Scalar:
    value: int

@dataclass
class ScalarSpec(FeatureSpec):
    value: RangeSpec

    def describe(self) -> str:
        return f"{self.__feature_name__} {self.value.describe()}"

    def instantiate(self, rng: random.Random) -> Scalar:
        return Scalar(self.value.sample(rng))
