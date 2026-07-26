from dataclasses import dataclass, field

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.spacing import Spacing


def join_copy_refs(refs: list[str]) -> str:
    """Join object refs as ``copies of A and B`` / ``copies of A, B, and C``."""
    if not refs:
        return "no items"
    if len(refs) == 1:
        return f"copies of {refs[0]}"
    if len(refs) == 2:
        return f"copies of {refs[0]} and {refs[1]}"
    *rest, last = refs
    return "copies of " + ", ".join(rest) + f", and {last}"


@register_feature("object.group")
@dataclass
class Group(Feature):
    """Composite object: a pool of items placed according to an arrangement."""

    arrangement: Feature
    pool: list[Feature] = field(default_factory=list)
    spacing: Spacing = field(default_factory=Spacing)

    def describe(self) -> str:
        refs = [item.refer() for item in self.pool]
        text = f"group of {join_copy_refs(refs)} arranged into {self.arrangement.describe()}"
        if not self.is_default("spacing"):
            spacing = self.spacing.describe()
            if spacing:
                text += f", {spacing}"
        return text
