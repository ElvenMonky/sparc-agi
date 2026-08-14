from dataclasses import dataclass

from sparc_agi.consts import MAX_DIRECTION, TRANSPARENT_COLOR
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import Access, register_feature, trait, with_article
from sparc_agi.puzzle_spec.features.cut import CutSpec
from sparc_agi.puzzle_spec.features.arrangement import OriginSpec, SizeSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, DirectionSpec, HeightSpec, WidthSpec
from sparc_agi.puzzle_spec.range import Range

@register_feature("object.point")
@dataclass
class PointSpec(ObjectSpec):
    origin: OriginSpec | None = trait(access=Access.GET, default=None)
    size: SizeSpec = trait(
        access=Access.GET,
        default_factory=lambda: SizeSpec(width=WidthSpec(Range(1)), height=HeightSpec(Range(1))),
    )

    def describe_head(
        self,
        ctx: Puzzle,
        *,
        count: Range | int | None = None,
        article: bool = False,
    ) -> str:
        head = self.kind_noun(count)
        if phrase := self.color.describe(ctx):
            head = f"{phrase} {head}"
        if article:
            head = with_article(head)
        return head

@dataclass
class GeometrySpec(ObjectSpec):
    fill_color: ColorSpec | None = trait(default=None)
    vertice_color: ColorSpec | None = trait(default=None)

@register_feature("object.line")
@dataclass
class LineSpec(GeometrySpec):
    direction: DirectionSpec = trait(default_factory=lambda: DirectionSpec(Range(0, MAX_DIRECTION)))

@register_feature("object.rectangle")
@dataclass
class RectangleSpec(GeometrySpec):
    cut: CutSpec = trait(default_factory=CutSpec)

    def describe(self, ctx: Puzzle, *, count: Range | int | None = None, article: bool = False) -> str:
        body = self.describe_head(ctx, count=count, article=article)
        if fill := self.fill_color:
            value = fill.value
            if value.lo == value.hi == TRANSPARENT_COLOR:
                body = body.replace("rectangle", "hollow rectangle", 1)
            elif color := fill.describe(ctx):
                body += f" with {color} interior"
            else:
                body += " with colored interior"
        if vertices := self.vertice_color:
            if color := vertices.describe(ctx):
                body += f" with {color} vertices"
            else:
                body += " with colored vertices"
        return body + self.describe_tail(ctx)
