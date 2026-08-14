from dataclasses import MISSING, dataclass, fields
from typing import Any, Callable, ClassVar, Self, TypeVar, get_args, get_origin

from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.wire import WireValue

@dataclass
class Transformation[Output: FeatureSpec]:
    REGISTRY: ClassVar[dict[str, type[Self]]] = {}

    @classmethod
    def tag(cls) -> str:
        for name, registered in Transformation.REGISTRY.items():
            if registered is cls:
                return name
        raise ValueError(f"{cls.__name__} is not registered")

    @classmethod
    def output_type(cls):
        for spec_cls in cls.__mro__:
            for base in getattr(spec_cls, "__orig_bases__", ()):
                origin = get_origin(base) or base
                if origin is Transformation:
                    args = get_args(base)
                    if len(args) == 1 and FeatureSpec.is_feature(args[0]):
                        return args[0]
                type_args = get_args(base)
                if not isinstance(origin, type) or not type_args:
                    continue
                for parent in getattr(origin, "__orig_bases__", ()):
                    parent_origin = get_origin(parent) or parent
                    if parent_origin is not Transformation:
                        continue
                    parent_args = get_args(parent)
                    if len(parent_args) != 1:
                        continue
                    output = parent_args[0]
                    if FeatureSpec.is_feature(output):
                        return output
                    specialized = type_args[0]
                    if FeatureSpec.is_feature(specialized):
                        return specialized
        raise ValueError(f"{cls.__name__} must specialize Transformation[FeatureSpec]")

    @classmethod
    def structure(cls, wires: object, _: type, __: Any) -> Self:
        if isinstance(wires, cls):
            return wires
        if not isinstance(wires, list):
            raise ValueError(f"{cls.__name__} wires must be a list, got {wires!r}")
        dc_fields = fields(cls)
        if not dc_fields:
            return cls()
        if get_origin(dc_fields[-1].type) is list:
            prefix_count = len(dc_fields) - 1
            if len(wires) < prefix_count:
                raise ValueError(
                    f"{cls.__name__} expects at least {prefix_count} wires, got {len(wires)!r}"
                )
            return cls(*wires[:prefix_count], wires[prefix_count:])
        if len(wires) != len(dc_fields):
            if len(wires) > len(dc_fields):
                raise ValueError(
                    f"{cls.__name__} expects at most {len(dc_fields)} wires, got {len(wires)!r}"
                )
            for dc_field in dc_fields[len(wires):]:
                if dc_field.default is MISSING and dc_field.default_factory is MISSING:
                    raise ValueError(
                        f"{cls.__name__} expects {len(dc_fields)} wires, got {len(wires)!r}"
                    )
        return cls(*wires)

    def unstructure(self) -> list[WireValue]:
        dc_fields = fields(self)
        if dc_fields and get_origin(dc_fields[-1].type) is list:
            wires = [getattr(self, dc_field.name) for dc_field in dc_fields[:-1]]
            wires.extend(getattr(self, dc_fields[-1].name))
        else:
            wires = [getattr(self, dc_field.name) for dc_field in dc_fields]
        while wires and wires[-1] is None:
            tail_field = dc_fields[len(wires) - 1]
            if tail_field.default is MISSING and tail_field.default_factory is MISSING:
                break
            wires.pop()
        return wires

    @classmethod
    def structure_step(cls, value: object, _: type, __: Any) -> Self:
        if isinstance(value, Transformation):
            return value
        if not isinstance(value, dict) or len(value) != 1:
            raise ValueError(f"step must be a single-key object, got {value!r}")
        (tag, wires), = value.items()
        spec_cls = Transformation.REGISTRY.get(tag)
        if spec_cls is None:
            raise ValueError(f"unknown transformation {tag!r}")
        return spec_cls.structure(wires, spec_cls, None)

    @classmethod
    def unstructure_step(cls, inst: Self) -> dict[str, list[WireValue]]:
        return {type(inst).tag(): inst.unstructure()}

    def alias_stem(self, **input: Any) -> str:
        return ""

    def describe(self, ctx: Puzzle, **input: Any) -> str:
        return ""

T = TypeVar("T", bound=Transformation)

def register_transformation(name: str) -> Callable[[type[T]], type[T]]:
    def decorator(spec_cls: type[T]) -> type[T]:
        if not issubclass(spec_cls, Transformation):
            raise TypeError(f"{spec_cls.__name__} must subclass Transformation")
        if name in Transformation.REGISTRY:
            raise ValueError(
                f"transformation {name!r} already registered as "
                f"{Transformation.REGISTRY[name].__name__}"
            )
        Transformation.REGISTRY[name] = spec_cls
        return spec_cls

    return decorator
