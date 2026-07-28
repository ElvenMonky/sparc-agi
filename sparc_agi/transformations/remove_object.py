from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sparc_agi.canvas import Geometry
from sparc_agi.features.base import Feature
from sparc_agi.features.objects.base import Object
from sparc_agi.features.objects.group import Group
from sparc_agi.features.objects.source import pool_member_via_source
from sparc_agi.transformations.base import Transformation, register_transformation
from sparc_agi.transformations.pick_object import _require_geometry_index


def _remove_from_group(group: Group, child: Object, *, step: int) -> Group:
    member = pool_member_via_source(child, group.pool)
    if member is None:
        raise ValueError(f"RemoveObject: {child.refer()} not found in {group.refer()}")
    new_pool = [item for item in group.pool if item is not member]
    out = group.derived(pool=new_pool)
    out.alias = f"group from step {step}"
    return out


@register_transformation("RemoveObject")
@dataclass
class RemoveObject(Transformation):
    """Drop one pool item from a group; inputs ``[object, object]`` → ``object``.

    Wires: ``[group, item_to_remove]``. Instantiate removes
    ``group.geometries[item.geometry_index]`` using the index stamped on ``item``
    by :class:`PickObject`.
    """

    input_features = ("object", "object")
    output_feature = "object"

    def apply(self, inputs: Sequence[Feature], *, step: int, **_: object) -> Feature:
        parent, child = inputs
        if not isinstance(parent, Group):
            raise TypeError(
                f"RemoveObject expects a group as first input, got {type(parent).__feature_name__}"
            )
        if type(child).__feature_family__ != "object":
            raise TypeError(
                f"RemoveObject expects an object to remove, got {type(child).__feature_name__}"
            )
        assert isinstance(child, Object)
        return _remove_from_group(parent, child, step=step)

    def instantiate(
        self,
        inputs: Sequence[Any],
        *,
        step: int,
        feature_inputs: Sequence[Feature] | None = None,
        feature_output: Feature | None = None,
    ) -> Geometry:
        del step, feature_output
        parent, _child = inputs
        if not isinstance(parent, Geometry):
            raise TypeError("RemoveObject.instantiate expects Geometry parent")
        if feature_inputs is None or len(feature_inputs) < 2:
            raise ValueError("RemoveObject.instantiate requires feature_inputs")
        index = _require_geometry_index(feature_inputs[1], who="RemoveObject.instantiate")
        return parent.without_index(index)

    def describe(self, inputs: Sequence[Feature], output: Feature, *, step: int) -> str:
        del output, step
        parent, child = inputs
        return f"Remove {child.refer()} from {parent.refer()}."
