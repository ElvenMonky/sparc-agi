from dataclasses import dataclass

from sparc_agi.transformations.base import Transformation, register_transformation

@register_transformation("RemoveObjects")
@dataclass
class RemoveObjects(Transformation):
    input_features = ("object", "filter")
    output_feature = "object"
