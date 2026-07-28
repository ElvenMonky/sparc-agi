from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sparc_agi.canvas import Geometry
from sparc_agi.features.base import Feature
from sparc_agi.features.filter import Filter
from sparc_agi.features.objects.base import Object
from sparc_agi.features.objects.group import Group
from sparc_agi.transformations.base import Transformation, register_transformation


def _require_geometry_index(feat: Feature | None, *, who: str) -> int:
    if feat is None or feat.geometry_index is None:
        raise ValueError(f"{who}: feature has no geometry_index")
    return feat.geometry_index


@register_transformation("PickObject")
@dataclass
class PickObject(Transformation):
    """Extract one pool item from a group; inputs ``[filter, object]`` → ``object``.

    ``apply`` records ``geometry_index`` = index of the match in ``group.pool``
    (and thus in the parent :class:`~sparc_agi.canvas.Geometry` children, which
    are placed in pool/sequence order). ``instantiate`` takes that child by index
    — no filter re-matching or fallbacks.
    """

    input_features = ("filter", "object")
    output_feature = "object"

    def apply(self, inputs: Sequence[Feature], *, step: int, **_: object) -> Feature:
        filt, obj = inputs
        if not isinstance(filt, Filter):
            raise TypeError(f"PickObject expects Filter, got {type(filt).__name__}")
        if not isinstance(obj, Group):
            raise TypeError(f"PickObject expects a group, got {type(obj).__feature_name__}")
        matches = [(i, item) for i, item in enumerate(obj.pool) if filt.matches(item)]
        if len(matches) != 1:
            criteria = ", ".join(m.refer() for _, m in matches) or "(none)"
            raise ValueError(
                f"PickObject expected exactly 1 match in {obj.refer()}, "
                f"got {len(matches)}: {criteria}"
            )
        index, item = matches[0]
        out = item.derived(geometry_index=index)
        out.alias = f"{out.kind_noun()} from step {step}"
        return out

    def instantiate(
        self,
        inputs: Sequence[Any],
        *,
        step: int,
        feature_inputs: Sequence[Feature] | None = None,
        feature_output: Feature | None = None,
    ) -> Geometry:
        del step, feature_inputs
        _filt_val, parent = inputs
        if not isinstance(parent, Geometry):
            raise TypeError(
                f"PickObject.instantiate expects Geometry, got {type(parent).__name__}"
            )
        index = _require_geometry_index(feature_output, who="PickObject.instantiate")
        return parent.child_at(index).as_root()

    def describe(self, inputs: Sequence[Feature], output: Feature, *, step: int) -> str:
        del output, step
        filt, obj = inputs
        if not isinstance(filt, Filter):
            raise TypeError(f"PickObject expects Filter, got {type(filt).__name__}")
        if filt.color is None and filt.kind is None:
            return f"Take the only object from {obj.refer()}."
        return f"Pick {filt.describe()} from {obj.refer()}."
