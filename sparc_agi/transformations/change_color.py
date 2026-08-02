from dataclasses import dataclass
from typing import Any

from sparc_agi.geometry import Geometry
from sparc_agi.features.base import Feature
from sparc_agi.features.scalars.color import Color
from sparc_agi.features.objects.base import Object
from sparc_agi.features.objects.group import Group
from sparc_agi.transformations.base import Transformation, register_transformation
from sparc_agi.transformations.pick_object import _require_geometry_index

def _recolor_object(obj: Object, color: Color) -> Object:
    """Set ``color`` on ``obj``, or recursively on a group's pool."""
    if obj.has_trait("color"):
        return obj.derived(color=color)
    if isinstance(obj, Group):
        return obj.derived(pool=[_recolor_object(item, color) for item in obj.pool])
    raise TypeError(f"cannot ChangeColor on {type(obj).__feature_name__} (no color trait)")

@register_transformation("ChangeColor")
@dataclass
class ChangeColor(Transformation):
    """Recolor an object; inputs ``[color, object]`` or ``[color, group, item]`` → ``object``.

    With two inputs, recolors ``object`` (and nested colored members).
    With three inputs, ``item`` must inherit (via ``source``) from a direct pool
    member of ``group``; instantiate recolors ``group.geometries[item.geometry_index]``.
    """

    input_features = ("color", "object")
    input_variadic = True
    output_feature = "object"

    @classmethod
    def check_arity(cls, n_inputs: int) -> None:
        if n_inputs not in (2, 3):
            raise ValueError(f"ChangeColor expects 2 or 3 input(s), got {n_inputs}")

    @classmethod
    def expected_input_family(cls, slot: int) -> str:
        if slot == 0:
            return "color"
        if slot in (1, 2):
            return "object"
        raise IndexError(f"ChangeColor has no input slot {slot}")

    def apply(self, inputs: list[Feature], *, step: int, **_: object) -> Feature:
        if len(inputs) == 2:
            color, obj = inputs
            if not isinstance(color, Color):
                raise TypeError(f"ChangeColor expects Color, got {type(color).__name__}")
            if type(obj).__feature_family__ != "object":
                raise TypeError(
                    f"ChangeColor expects an object, got {type(obj).__feature_name__}"
                )
            assert isinstance(obj, Object)
            out = _recolor_object(obj, color)
            out.alias = f"{out.kind_noun()} from step {step}"
            return out

        color, group, item = inputs
        if not isinstance(color, Color):
            raise TypeError(f"ChangeColor expects Color, got {type(color).__name__}")
        if not isinstance(group, Group):
            raise TypeError(
                f"ChangeColor with 3 inputs expects a group as second input, "
                f"got {type(group).__feature_name__}"
            )
        if type(item).__feature_family__ != "object":
            raise TypeError(
                f"ChangeColor expects an object as third input, got {type(item).__feature_name__}"
            )
        assert isinstance(item, Object)
        member = pool_member_via_source(item, group.pool)
        if member is None:
            raise ValueError(
                f"ChangeColor: {item.refer()} does not inherit from a pool member of {group.refer()}"
            )
        if item.geometry_index is None:
            raise ValueError(
                f"ChangeColor: {item.refer()} has no geometry_index (pick it first)"
            )
        new_pool = [
            _recolor_object(m, color) if m is member else m for m in group.pool
        ]
        out = group.derived(pool=new_pool)
        out.alias = f"group from step {step}"
        return out

    def instantiate(
        self,
        inputs: list[Any],
        *,
        step: int,
        feature_inputs: list[Feature] | None = None,
        feature_output: Feature | None = None,
    ) -> Geometry:
        del step, feature_output
        if len(inputs) == 2:
            color, obj = inputs
            if not isinstance(color, int) or not isinstance(obj, Geometry):
                raise TypeError("ChangeColor.instantiate expects int color and Geometry")
            return obj.recolor(color)

        color, group, _item = inputs
        if not isinstance(color, int):
            raise TypeError("ChangeColor.instantiate expects int color")
        if not isinstance(group, Geometry):
            raise TypeError("ChangeColor.instantiate expects Geometry group")
        if feature_inputs is None or len(feature_inputs) < 3:
            raise ValueError("ChangeColor.instantiate requires feature_inputs for 3-arg form")
        index = _require_geometry_index(feature_inputs[2], who="ChangeColor.instantiate")
        child = group.child_at(index)
        return group.replace_index(index, child.recolor(color))

    def describe(self, inputs: list[Feature], output: Feature, *, step: int) -> str:
        del output, step
        if len(inputs) == 2:
            color, obj = inputs
            return f"Change color of {obj.refer()} to {color.refer()}."
        color, group, item = inputs
        return f"Change color of {item.refer()} in {group.refer()} to {color.refer()}."
