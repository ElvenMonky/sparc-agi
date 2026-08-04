from dataclasses import dataclass

from sparc_agi.transformations.base import Transformation, register_transformation

@register_transformation("ExtractMappedColor")
@dataclass
class ExtractMappedColor(Transformation):
    input_features = ("object",)
    output_feature = "color"
