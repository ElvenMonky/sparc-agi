from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sparc_agi.features.base import Feature
from sparc_agi.features.group import Group, join_copy_refs
from sparc_agi.grid import Grid, Placement, compose_placements
from sparc_agi.transformations.base import Transformation, register_transformation


@register_transformation("ArrangeObjects")
@dataclass
class ArrangeObjects(Transformation):
    """Place one or more objects onto an arrangement → ``object.group``.

    Inputs: ``[arrangement, object, object?, ...]`` (variadic object slots).
    The object inputs are stored unchanged as the group's pool; the arrangement
    (and its sequence) decides how copies of those items are laid out.
    """

    input_features = ("arrangement", "object")
    input_variadic = True
    output_feature = "object"

    def apply(self, inputs: Sequence[Feature], *, step: int, **_: object) -> Feature:
        arrangement, *objects = inputs
        if type(arrangement).__feature_family__ != "arrangement":
            raise TypeError(
                f"ArrangeObjects expects an arrangement feature, got {type(arrangement).__feature_name__}"
            )
        if not objects:
            raise ValueError("ArrangeObjects requires at least one object")
        for obj in objects:
            if type(obj).__feature_family__ != "object":
                raise TypeError(
                    f"ArrangeObjects expects object features, got {type(obj).__feature_name__}"
                )

        out = Group(arrangement=arrangement, pool=list(objects))
        out.alias = f"group from step {step}"
        return out

    def instantiate(self, inputs: Sequence[Any], *, step: int) -> Grid:
        del step
        arrangement, *objects = inputs
        if not isinstance(arrangement, list):
            raise TypeError(
                f"ArrangeObjects.instantiate expects placement list, got {type(arrangement).__name__}"
            )
        if not objects:
            raise ValueError("ArrangeObjects requires at least one object grid")
        for obj in objects:
            if not isinstance(obj, list):
                raise TypeError(
                    f"ArrangeObjects.instantiate expects object grids, got {type(obj).__name__}"
                )
        placements: list[Placement] = arrangement
        return compose_placements(placements, list(objects))

    def describe(self, inputs: Sequence[Feature], output: Feature, *, step: int) -> str:
        del output, step
        arrangement, *objects = inputs
        refs = [obj.refer() for obj in objects]
        return f"Arrange {join_copy_refs(refs)} into {arrangement.describe()}."
