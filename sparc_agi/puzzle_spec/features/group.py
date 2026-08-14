from dataclasses import dataclass

from sparc_agi.consts import MAX_COLOR, MAX_COUNT
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import Access, register_feature, trait, with_article
from sparc_agi.puzzle_spec.features.arrangement import (
    ArrangementSlotSpec,
    ArrangementSpec,
    GridArrangementSpec,
    SizeSpec,
    TreeArrangementSpec,
)
from sparc_agi.puzzle_spec.features.geometry import PointSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.features.pattern import PatternSlotSpec, PatternSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, CountSpec, HeightSpec, WidthSpec
from sparc_agi.puzzle_spec.range import Range

def pool_copy_phrase(refs: list[str]) -> str:
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
class GroupSpec(ObjectSpec):
    count: CountSpec = trait(default_factory=CountSpec)
    draft: PatternSpec | None = trait(default=None)
    pool: list[PoolItemSpec] = trait(access=Access.SET, default_factory=list)

    def describe(self, ctx: Puzzle, *, count: Range | int | None = None, article: bool = True) -> str:
        group_count = self.count.value
        prefix = self.draft.prefix if self.draft else []
        parts: list[str] = []
        for index in prefix:
            if index < len(self.pool) and (member := self.pool[index].value) is not None:
                parts.append(member.describe(ctx, article=True))
        remaining = Range(
            max(0, group_count.lo - len(prefix)),
            max(0, group_count.hi - len(prefix)),
            group_count.step,
        )
        if remaining.hi > 0:
            members = " and ".join(
                item.value.describe(ctx, count=remaining)
                for item in self.pool
                if item.value is not None
            )
            phrase = f"{self.kind_noun(count)} of {remaining.describe()} {members}"
            parts.append(with_article(phrase) if article else phrase)
        head = " and ".join(parts)
        if size := self.size.describe(ctx):
            head += f" within {size} area"
        return head

@register_feature("object.grid")
@dataclass
class GridSpec(GroupSpec):
    arrangement: ArrangementSlotSpec = trait(default_factory=lambda: ArrangementSlotSpec(GridArrangementSpec()))
    pattern: PatternSlotSpec | None = trait(default=None)

    def _has_custom_pool(self) -> bool:
        return bool(self.pool)

    def describe(self, ctx: Puzzle, *, count: Range | int | None = None, article: bool = False) -> str:
        body = self.describe_head(ctx, count=count, article=article) + self.describe_tail(ctx)
        if self._has_custom_pool():
            arrangement_count = (
                self.arrangement.value.count.value
                if self.arrangement.value.count is not None
                else None
            )
            pool_parts: list[str] = []
            for item in self.pool:
                if item.value is None:
                    continue
                if item.variants == Range(1):
                    ref = pool_copy_phrase([item.value.describe(ctx, article=True)])
                else:
                    ref = item.value.describe(ctx, count=arrangement_count)
                pool_parts.append(ref)
            members = " and ".join(pool_parts)
            verb = "consist" if self.is_plural(count) else "consists"
            if arrangement_count is not None:
                body += f" that {verb} of {arrangement_count.describe()} {members}"
            else:
                body += f" that {verb} of {members}"
            if self.pattern is not None and self.pattern.value is not None:
                if desc := self.pattern.value.refer(ctx):
                    body += f" using {desc}"
        return body

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

    def _has_custom_pool(self) -> bool:
        return False

@register_feature("object.sprite")
@dataclass
class SpriteSpec(GroupSpec):
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
class TreeStructureSpec(GridSpec):
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
