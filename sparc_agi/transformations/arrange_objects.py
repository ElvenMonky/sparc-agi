from dataclasses import dataclass

from sparc_agi.transformations.base import Transformation, register_transformation


@register_transformation("ArrangeObjects")
@dataclass
class ArrangeObjects(Transformation):
    """Place one or more objects onto an arrangement → ``object``.

    Inputs: ``[arrangement, object, object?, ...]`` (variadic object slots).
    Sequence cycles in the arrangement index into those object slots.
    """

    input_features = ("arrangement", "object")
    input_variadic = True
    output_feature = "object"
