from dataclasses import dataclass

from sparc_agi.transformations.base import Transformation, register_transformation

@register_transformation("ArrangeObjects")
@dataclass
class ArrangeObjects(Transformation):
    input_features = ("layout", "object")
    input_variadic = True
    output_feature = "object"
