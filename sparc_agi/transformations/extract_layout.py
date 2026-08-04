from dataclasses import dataclass

from sparc_agi.transformations.base import Transformation, register_transformation

@register_transformation("ExtractLayout")
@dataclass
class ExtractLayout(Transformation):
    input_features = ("object",)
    output_feature = "layout"
