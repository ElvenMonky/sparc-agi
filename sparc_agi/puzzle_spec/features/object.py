from dataclasses import dataclass, field

from sparc_agi.consts import MAX_COLOR, MAX_COUNT, TRANSPARENT_COLOR
from sparc_agi.puzzle_spec.context import PuzzleContext
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.features.cut import CutSpec
from sparc_agi.puzzle_spec.features.arrangement import (
    ArrangementSlotSpec,
    ArrangementSpec,
    GridArrangementSpec,
    OriginSpec,
    SizeSpec,
    TreeArrangementSpec,
)
from sparc_agi.puzzle_spec.features.pattern import PatternSlotSpec, PatternSpec
from sparc_agi.puzzle_spec.features.margin import MarginSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, CountSpec, HeightSpec, OrientationSpec, WidthSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

def with_article(phrase: str) -> str:
    if phrase[:1].lower() in "aeiou":
        return f"an {phrase}"
    return f"a {phrase}"

@register_feature("object")
@dataclass
class ObjectSpec(FeatureSpec):
    color: ColorSpec = trait(default_factory=lambda: ColorSpec(value=Range(1, MAX_COLOR)))
    margin: MarginSpec = trait(default_factory=MarginSpec)
    orientation: OrientationSpec | None = trait(default=None)
    origin: OriginSpec | None = trait(default=None)
    size: SizeSpec = trait(default_factory=SizeSpec)
    linked_mappings: list[str] = field(default_factory=list)

    def describe_head(
        self,
        ctx: PuzzleContext,
        *,
        count: Range | int | None = None,
        article: bool = False,
    ) -> str:
        head = self.kind_noun(count)
        if size := self.size.describe(ctx):
            head = f"{size} {head}"
        if phrase := self.color.describe(ctx):
            head = f"{phrase} {head}"
        if article:
            head = with_article(head)
        return head

    def describe_tail(self, ctx: PuzzleContext) -> str:
        if self.origin is not None:
            return self.origin.describe(ctx)
        return ""

    def describe(self, ctx: PuzzleContext, *, count: Range | int | None = None, article: bool = False) -> str:
        return self.describe_head(ctx, count=count, article=article) + self.describe_tail(ctx)

@dataclass
class PoolItemSpec(FeatureSlotSpec[ObjectSpec]):
    value: ObjectSpec | None = None
    variants: Range[1, MAX_COUNT] | None = None

@register_feature("object.point")
@dataclass
class PointSpec(ObjectSpec):
    origin: OriginSpec | None = trait(access=Access.GET, default=None)
    size: SizeSpec = trait(
        access=Access.GET,
        default_factory=lambda: SizeSpec(width=WidthSpec(Range(1)), height=HeightSpec(Range(1))),
    )

@dataclass
class GeometrySpec(ObjectSpec):
    fill_color: ColorSpec | None = trait(default=None)
    vertice_color: ColorSpec | None = trait(default=None)

@register_feature("object.line")
@dataclass
class LineSpec(GeometrySpec):
    direction: OrientationSpec = trait(default_factory=lambda: OrientationSpec(Range(0)))

@register_feature("object.rectangle")
@dataclass
class RectangleSpec(GeometrySpec):
    cut: CutSpec = trait(default_factory=CutSpec)

    def describe(self, ctx: PuzzleContext, *, count: Range | int | None = None, article: bool = False) -> str:
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

@dataclass
class BaseGroupSpec(ObjectSpec):
    pool: list[PoolItemSpec] = trait(access=Access.SET, default_factory=list)

@register_feature("object.group")
@dataclass
class GroupSpec(BaseGroupSpec):
    count: CountSpec = trait(default_factory=CountSpec)
    draft: PatternSpec | None = trait(default=None)

    def describe(self, ctx: PuzzleContext) -> str:
        count = self.count.value
        prefix = self.draft.prefix if self.draft else []
        parts: list[str] = []
        for index in prefix:
            if index < len(self.pool) and (member := self.pool[index].value) is not None:
                parts.append(member.describe(ctx, article=True))
        remaining = Range(
            max(0, count.lo - len(prefix)),
            max(0, count.hi - len(prefix)),
            count.step,
        )
        if remaining.hi > 0:
            members = " and ".join(
                item.value.describe(ctx, count=remaining)
                for item in self.pool
                if item.value is not None
            )
            parts.append(with_article(f"group of {remaining.describe()} {members}"))
        head = " and ".join(parts)
        if size := self.size.describe(ctx):
            head += f" within {size} area"
        return head

@register_feature("object.grid")
@dataclass
class GridSpec(BaseGroupSpec):
    arrangement: ArrangementSlotSpec = trait(default_factory=ArrangementSlotSpec(GridArrangementSpec()))
    pattern: PatternSlotSpec | None = trait(default=None)
    mask: PatternSpec | None = trait(access=Access.GET, default=None)

@register_feature("object.glyph")
@dataclass
class GlyphSpec(GridSpec):
    size: SizeSpec = trait(
        access=Access.GET,
        default_factory=lambda: SizeSpec(width=WidthSpec(Range(3)), height=HeightSpec(Range(3))),
    )
    arrangement: ArrangementSlotSpec = trait(
        access=Access.GET,
        default_factory=lambda: ArrangementSlotSpec(ArrangementSpec(count=CountSpec(Range(2, 8)))),
    )
    pool: list[PoolItemSpec] = trait(access=Access(0), default_factory=list)

    def __post_init__(self) -> None:
        self.arrangement.value.size = self.size
        self.pool = [PoolItemSpec(
            variants=Range(1),
            value=PointSpec(color=self.color),
        )]

@register_feature("object.sprite")
@dataclass
class SpriteSpec(BaseGroupSpec):
    color: ColorSpec = trait(
        access=Access.SET,
        default_factory=ColorSpec,
    )
    pool: list[PoolItemSpec] = trait(access=Access(0), default_factory=list)

    def __post_init__(self) -> None:
        value = self.color.value
        if value.lo < 0 or value.hi > MAX_COLOR:
            raise ValueError(f"sprite color must be in 0..{MAX_COLOR}, got {value.describe()}")
        if len(range(value.lo, value.hi + 1, value.step)) < 2:
            raise ValueError(f"sprite color must allow at least 2 colors, got {value.describe()}")
        self.pool = [PoolItemSpec(value=PointSpec(color=self.color))]

@register_feature("object.tree_structure")
@dataclass
class TreeStructureSpec(BaseGroupSpec):
    count: CountSpec = trait(default_factory=CountSpec)
    arrangement: ArrangementSlotSpec = trait(
        access=Access.GET,
        default_factory=lambda: ArrangementSlotSpec(TreeArrangementSpec()),
    )
    pool: list[PoolItemSpec] = trait(access=Access.SET, default_factory=list)

    def __post_init__(self) -> None:
        self.arrangement.value.count = self.count
        if len(self.pool) == 0:
            self.pool = [PoolItemSpec(
                variants=Range(1),
                value=PointSpec(color=self.color),
            )]

    def _has_custom_pool(self) -> bool:
        if len(self.pool) != 1:
            return True
        item = self.pool[0]
        if item.variants != Range(1):
            return True
        value = item.value
        if not isinstance(value, PointSpec):
            return True
        return value.color != self.color

    def describe(self, ctx: PuzzleContext, *, count: Range | int | None = None, article: bool = False) -> str:
        body = self.describe_head(ctx, count=count, article=article) + self.describe_tail(ctx)
        if self._has_custom_pool():
            members = " and ".join(
                item.value.describe(ctx, count=self.count.value)
                for item in self.pool
                if item.value is not None
            )
            verb = "consist" if self.is_plural(count) else "consists"
            body += f" that {verb} of {self.count.value.describe()} {members}"
        return body
