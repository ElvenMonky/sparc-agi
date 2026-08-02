from dataclasses import dataclass
from typing import Any

from sparc_agi.geometry import Geometry
from sparc_agi.features.base import Feature
from sparc_agi.features.objects.base import Object
from sparc_agi.transformations.base import Transformation, register_transformation

@register_transformation("RemoveObject")
@dataclass
class RemoveObject(Transformation):
    input_features = ("object", "object")
    output_feature = "object"

    def apply(self, inputs: list[FeatureSpec], *, step: int, **_: object) -> Feature:
        parent, child = inputs
        if type(child).__feature_family__ != "object":
            raise TypeError(
                f"RemoveObject expects an object to remove, got {type(child).__feature_name__}"
            )
        assert isinstance(child, Object)
        out = parent.derived(pool=[item for item in parent.pool if item is not child])
        out.alias = f"{parent.kind_noun()} from step {step}"
        return out

    def instantiate(
        self,
        inputs: list[Feature],
        *,
        step: int,
        feature_inputs: list[FeatureSpec] | None = None,
        feature_output: FeatureSpec | None = None,
    ) -> Geometry:
        parent, _child = inputs
        index = feature_inputs[0].pool.index(feature_inputs[1])
        return parent.without_index(index)

    def describe(self, inputs: list[FeatureSpec], output: FeatureSpec, *, step: int) -> str:
        parent, child = inputs
        return f"Remove {child.refer()} from {parent.refer()}."
