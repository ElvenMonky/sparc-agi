"""cattrs converter for puzzle source documents.

Source shape (per puzzle id)::

    {
      "cache": { "<key>": { "<feature.name>": <payload> }, ... },
      "input": { "<feature.name>": <payload> },
      "samples": { "train": <range>, "test": <range> },
      "palette": { "<logical>": <display>, ... },  // optional fixed colors
      "skeleton": [
        { "<Transform>": [<wire>, ...] },
        // or equivalently:
        { "type": "<Transform>", "input": [<wire>, ...] }
      ]
    }

New features / transformations only need a registered class; this module's
hooks resolve tags through the registries and do not hard-code type names.
"""

import json
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints

import cattrs
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override

from sparc_agi.features import FEATURE_REGISTRY, FeatureSpec, Size, feature_family
from sparc_agi.features.cut import Cut
from sparc_agi.features.filter import FilterSpec
from sparc_agi.features.layouts.base import LayoutSpec
from sparc_agi.features.scalars.base import ScalarSpec
from sparc_agi.features.scalars.height import HeightSpec
from sparc_agi.features.objects.base import ObjectSpec, PoolItem
from sparc_agi.features.patterns.base import PatternSpec
from sparc_agi.range import Range
from sparc_agi.features.spacing import Gap, Margin
from sparc_agi.features.scalars.width import WidthSpec
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.puzzle import CacheItem, PuzzleSpec
from sparc_agi.transformations import TRANSFORMATION_REGISTRY, Transformation

converter = cattrs.Converter()

def _is_scalar_feature_type(t: Any) -> bool:
    return isinstance(t, type) and issubclass(t, ScalarSpec) and t is not ScalarSpec

def _is_plain_dataclass(t: Any) -> bool:
    return (
        is_dataclass(t)
        and isinstance(t, type)
        and t not in (Size, Range, Cut, Gap, Margin)
        and not issubclass(t, FeatureSpec)
    )

# Plain nested dataclasses on demand. Size / Range / Features have dedicated hooks.
converter.register_structure_hook_factory(
    _is_plain_dataclass,
    lambda t: make_dict_structure_fn(t, converter),
)
converter.register_unstructure_hook_factory(
    _is_plain_dataclass,
    lambda t: make_dict_unstructure_fn(t, converter),
)

def structure_range(obj: Any, _type: type) -> Range:
    return Range.from_raw(obj)

def unstructure_range(obj: Range) -> int | list[int]:
    return obj.to_raw()

converter.register_structure_hook(Range, structure_range)
converter.register_unstructure_hook(Range, unstructure_range)

def structure_gap_spec(obj: Any, _type: type) -> Gap:
    return Gap.from_raw(obj)

def unstructure_gap_spec(obj: Gap) -> int | list[int] | dict[str, int | list[int]]:
    return obj.to_raw()

def structure_margin_spec(obj: Any, _type: type) -> Margin:
    return Margin.from_raw(obj)

def unstructure_margin_spec(
    obj: Margin,
) -> int | list[int] | dict[str, int | list[int]]:
    return obj.to_raw()

converter.register_structure_hook(Gap, structure_gap_spec)
converter.register_unstructure_hook(Gap, unstructure_gap_spec)
converter.register_structure_hook(Margin, structure_margin_spec)
converter.register_unstructure_hook(Margin, unstructure_margin_spec)
converter.register_structure_hook(Cut, lambda obj, _type: Cut.from_raw(obj))
converter.register_unstructure_hook(Cut, lambda obj: obj.to_raw())

def structure_scalar_feature(obj: Any, cls: type[FeatureSpec]) -> FeatureSpec:
    """Structure a concrete scalar feature from a bare Range payload (or instance)."""
    if isinstance(obj, cls):
        return obj
    return cls(value=converter.structure(obj, Range))

converter.register_structure_hook_func(_is_scalar_feature_type, structure_scalar_feature)

def _is_composite_feature_type(t: Any) -> bool:
    return (
        isinstance(t, type)
        and issubclass(t, FeatureSpec)
        and t is not FeatureSpec
        and not issubclass(t, ScalarSpec)
    )

def structure_composite_feature(obj: Any, cls: type[FeatureSpec]) -> FeatureSpec:
    """Structure a concrete composite feature from its bare payload object."""
    if isinstance(obj, cls):
        return obj
    return _structure_concrete(obj, cls)

converter.register_structure_hook_func(_is_composite_feature_type, structure_composite_feature)

def _structure_nested_scalar(payload: Any, cls: type[FeatureSpec]) -> FeatureSpec:
    """Structure a scalar feature nested under a field (bare payload, not tagged)."""
    return structure_scalar_feature(payload, cls)

def structure_size(obj: Any, _type: type) -> Size:
    if not isinstance(obj, dict):
        raise ValueError(f"size must be an object, got {obj!r}")
    try:
        size = Size(
            width=_structure_nested_scalar(obj["width"], WidthSpec),
            height=_structure_nested_scalar(obj["height"], HeightSpec),
        )
        if "ratio" in obj:
            size.ratio = converter.structure(obj["ratio"], Range)
        return size
    except KeyError as exc:
        raise ValueError(f"size requires 'width' and 'height', got {obj!r}") from exc

def unstructure_size(obj: Size) -> dict[str, int | list[int]]:
    # Nested form keeps bare range payloads; tagged form is only for FeatureSpec slots.
    payload = {
        "width": converter.unstructure(obj.width.value),
        "height": converter.unstructure(obj.height.value),
    }
    if obj.ratio is not None:
        payload["ratio"] = converter.unstructure(obj.ratio)
    return payload

converter.register_structure_hook(Size, structure_size)
converter.register_unstructure_hook(Size, unstructure_size)

def _require_single_tag(obj: Any, kind: str) -> tuple[str, Any]:
    if not isinstance(obj, dict) or len(obj) != 1:
        raise ValueError(f"{kind} must be a single-key object, got {obj!r}")
    ((tag, payload),) = obj.items()
    if not isinstance(tag, str):
        raise ValueError(f"{kind} tag must be a string, got {tag!r}")
    return tag, payload

def _normalize_composite_payload(payload: dict[str, Any], cls: type[FeatureSpec]) -> dict[str, Any]:
    """Map flat child tags onto field names.

    When a payload key is a registered feature tag whose family matches a field
    name (e.g. ``object.sprite`` → field ``object``), rewrite it to a tagged
    nested value so polymorphic ``FeatureSpec`` slots keep their kind.
    """
    hints = get_type_hints(cls)
    field_names = set(cls.trait_names())
    out = dict(payload)
    for key in list(out):
        if key in field_names or key not in FEATURE_REGISTRY:
            continue
        family = feature_family(key)
        if family not in field_names or family in out:
            continue
        child_payload = out.pop(key)
        ann = hints.get(family)
        if ann is FeatureSpec:
            out[family] = {key: child_payload}
        else:
            expected = getattr(ann, "__feature_name__", None)
            out[family] = child_payload if expected == key else {key: child_payload}
    return out

def _structure_concrete(payload: Any, cls: type) -> Any:
    """Structure into a concrete dataclass without re-entering tagged-union hooks."""
    if (
        isinstance(payload, dict)
        and isinstance(cls, type)
        and issubclass(cls, FeatureSpec)
        and not issubclass(cls, ScalarSpec)
    ):
        payload = _normalize_composite_payload(payload, cls)
    kwargs: dict[str, Any] = {}
    if isinstance(cls, type) and issubclass(cls, FeatureSpec):
        # Runtime-only fields. ``source`` is *not* omitted: bible may set cache keys.
        kwargs["alias"] = override(omit=True)
        kwargs["geometry_index"] = override(omit=True)
    return make_dict_structure_fn(cls, converter, **kwargs)(payload, cls)

def structure_feature(obj: Any, _type: type) -> FeatureSpec:
    tag, payload = _require_single_tag(obj, "feature")
    try:
        cls = FEATURE_REGISTRY[tag]
    except KeyError as exc:
        known = ", ".join(sorted(FEATURE_REGISTRY)) or "(none)"
        raise ValueError(f"unknown feature {tag!r}; registered: {known}") from exc

    if issubclass(cls, ScalarSpec):
        return structure_scalar_feature(payload, cls)
    if cls is FilterSpec:
        return FilterSpec(
            index=payload.get("index"),
            criteria=list(payload.get("criteria", [])),
            values=dict(payload.get("values", {})),
        )
    return _structure_concrete(payload, cls)

def _unstructure_composite_payload(obj: FeatureSpec) -> dict[str, Any]:
    """Unstructure composite feature fields; nested scalars stay bare (untagged)."""
    cls = type(obj)
    hints = get_type_hints(cls)
    payload: dict[str, Any] = {}
    for f in fields(cls):
        if f.name not in cls.trait_names():
            continue
        val = getattr(obj, f.name)
        if val is None:
            continue
        # Omit nested defaults (e.g. LayoutSpec.spacing, PatternSpec.prefix).
        if f.default_factory is not MISSING and val == f.default_factory():
            continue
        if f.default is not MISSING and val == f.default:
            continue
        if isinstance(val, ScalarSpec):
            payload[f.name] = converter.unstructure(val.value)
        elif isinstance(val, FeatureSpec):
            tagged = unstructure_feature(val)
            ((tag, inner),) = tagged.items()
            # Field name matches tag → bare payload; polymorphic slot → flat kind tag.
            ann = hints.get(f.name)
            if tag == f.name:
                payload[f.name] = inner
            elif ann in (FeatureSpec, LayoutSpec, ObjectSpec):
                payload[tag] = inner
            else:
                payload[f.name] = tagged
        else:
            payload[f.name] = converter.unstructure(val)
    # ``source`` is not a trait (inheritance), but bible cache keys round-trip.
    src = obj.source
    if isinstance(src, str):
        payload["source"] = src
    elif isinstance(src, list) and src and all(isinstance(k, str) for k in src):
        payload["source"] = list(src)
    return payload

def unstructure_feature(obj: FeatureSpec) -> dict[str, Any]:
    cls = type(obj)
    if isinstance(obj, ScalarSpec):
        payload: Any = converter.unstructure(obj.value)
    else:
        payload = _unstructure_composite_payload(obj)
    return {cls.__feature_name__: payload}

def structure_transformation(obj: Any, _type: type) -> Transformation:
    tag, inputs = _require_single_tag(obj, "transformation")
    try:
        cls = TRANSFORMATION_REGISTRY[tag]
    except KeyError as exc:
        known = ", ".join(sorted(TRANSFORMATION_REGISTRY)) or "(none)"
        raise ValueError(f"unknown transformation {tag!r}; registered: {known}") from exc
    if not isinstance(inputs, list):
        raise ValueError(f"transformation {tag!r} inputs must be a list, got {inputs!r}")
    for wire in inputs:
        if isinstance(wire, bool) or not isinstance(wire, (str, int)):
            raise ValueError(f"wire reference must be a string or integer, got {wire!r}")
    cls.check_arity(len(inputs))
    return cls(inputs=list(inputs))

def unstructure_transformation(obj: Transformation) -> dict[str, list[str | int]]:
    return {type(obj).__transformation_name__: list(obj.inputs)}

converter.register_structure_hook_func(lambda t: t is FeatureSpec, structure_feature)
converter.register_structure_hook_func(lambda t: t is Transformation, structure_transformation)

def structure_layout(obj: Any, _type: type) -> LayoutSpec:
    feat = structure_feature(obj, FeatureSpec)
    if type(feat).__feature_family__ != "layout":
        raise ValueError(
            f"expected a layout feature, got {type(feat).__feature_name__}"
        )
    assert isinstance(feat, LayoutSpec)
    return feat

def structure_pattern(obj: Any, _type: type) -> PatternSpec:
    if not isinstance(obj, dict) or len(obj) != 1:
        return _structure_concrete(obj, PatternSpec)
    tag = next(iter(obj))
    if not isinstance(tag, str) or not tag.startswith("pattern."):
        return _structure_concrete(obj, PatternSpec)
    feat = structure_feature(obj, FeatureSpec)
    if type(feat).__feature_family__ != "pattern":
        raise ValueError(f"expected a pattern feature, got {type(feat).__feature_name__}")
    assert isinstance(feat, PatternSpec)
    return feat

def structure_object(obj: Any, _type: type) -> ObjectSpec:
    """Tagged object union (``object.sprite``, ``object.group``, …)."""
    feat = structure_feature(obj, FeatureSpec)
    if type(feat).__feature_family__ != "object":
        raise ValueError(f"expected an object feature, got {type(feat).__feature_name__}")
    assert isinstance(feat, ObjectSpec)
    return feat

def _is_pool_item_list(t: Any) -> bool:
    return get_origin(t) is list and get_args(t) == (PoolItem,)

def structure_pool_item_list(obj: Any, _type: type) -> list[PoolItem]:
    if not isinstance(obj, list):
        raise ValueError(f"object pool must be a list, got {obj!r}")
    return [structure_pool_item(item, PoolItem) for item in obj]

def structure_pool_item(obj: Any, _type: type) -> PoolItem:
    if not isinstance(obj, dict):
        raise ValueError(f"pool item must be an object, got {obj!r}")
    data = dict(obj)
    variants = data.pop("variants", None)
    if variants is not None and (isinstance(variants, bool) or not isinstance(variants, int)):
        raise ValueError(f"pool item variants must be an integer or null, got {variants!r}")
    return PoolItem(object=structure_object(data, ObjectSpec), variants=variants)

converter.register_structure_hook_func(lambda t: t is LayoutSpec, structure_layout)
converter.register_structure_hook_func(lambda t: t is PatternSpec, structure_pattern)
converter.register_structure_hook_func(lambda t: t is ObjectSpec, structure_object)
converter.register_structure_hook(PoolItem, structure_pool_item)
converter.register_structure_hook_func(_is_pool_item_list, structure_pool_item_list)

converter.register_unstructure_hook_func(
    lambda cls: isinstance(cls, type) and issubclass(cls, FeatureSpec),
    unstructure_feature,
)
converter.register_unstructure_hook_func(
    lambda cls: isinstance(cls, type) and issubclass(cls, Transformation),
    unstructure_transformation,
)
def _is_int_int_dict(t: Any) -> bool:
    return get_origin(t) is dict and get_args(t) == (int, int)

def _structure_int_int_dict(obj: Any, _type: type) -> dict[int, int]:
    """JSON object keys are strings; coerce ``{\"0\": 0}`` → ``{0: 0}``."""
    if not isinstance(obj, dict):
        raise ValueError(f"expected object, got {obj!r}")
    out: dict[int, int] = {}
    for key, val in obj.items():
        try:
            ikey = int(key)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"dict key must be an int, got {key!r}") from exc
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(f"dict value must be an int, got {val!r}")
        out[ikey] = val
    return out

converter.register_structure_hook_func(_is_int_int_dict, _structure_int_int_dict)

def structure_cache_item(obj: Any, _type: type) -> CacheItem:
    if not isinstance(obj, dict):
        raise ValueError(f"cache item must be an object, got {obj!r}")
    data = dict(obj)
    scope = data.pop("scope", "puzzle")
    if scope not in ("puzzle", "sample"):
        raise ValueError(f"cache item scope must be 'puzzle' or 'sample', got {scope!r}")
    return CacheItem(feature=structure_feature(data, FeatureSpec), scope=scope)

converter.register_structure_hook(
    PaletteSpec,
    lambda obj, _type: PaletteSpec(fixed=_structure_int_int_dict(obj, dict[int, int])),
)
converter.register_structure_hook(CacheItem, structure_cache_item)
converter.register_structure_hook(PuzzleSpec, make_dict_structure_fn(PuzzleSpec, converter))

def structure_puzzle(obj: Any) -> PuzzleSpec:
    if not isinstance(obj, dict):
        raise ValueError(f"puzzle must be an object, got {type(obj).__name__}")
    return converter.structure(obj, PuzzleSpec)

def load_puzzle(path: Union[str, Path], puzzle_id: str) -> PuzzleSpec:
    with Path(path).open() as f:
        source = json.load(f)
    if not isinstance(source, dict):
        raise ValueError(f"source must be an object, got {type(source).__name__}")
    try:
        puzzle = source[puzzle_id]
    except KeyError as exc:
        raise KeyError(f"unknown puzzle id {puzzle_id!r}") from exc
    return structure_puzzle(puzzle)
