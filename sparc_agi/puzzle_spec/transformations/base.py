from dataclasses import MISSING, dataclass, fields
from typing import Any, Callable, ClassVar, Self, TypeVar, get_args, get_origin

from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.wire import WireValue

def _is_concrete_output(typ) -> bool:
    if isinstance(typ, type):
        return issubclass(typ, FeatureSpec)
    args = get_args(typ)
    if not args:
        return False
    return all(
        arg is type(None) or (isinstance(arg, type) and issubclass(arg, FeatureSpec))
        for arg in args
    )

@dataclass
class TransformationSpec[Output: FeatureSpec]:
    REGISTRY: ClassVar[dict[str, type[Self]]] = {}

    @classmethod
    def tag(cls) -> str:
        for name, registered in TransformationSpec.REGISTRY.items():
            if registered is cls:
                return name
        raise ValueError(f"{cls.__name__} is not registered")

    @classmethod
    def output_type(cls):
        for spec_cls in cls.__mro__:
            for base in getattr(spec_cls, "__orig_bases__", ()):
                origin = get_origin(base) or base
                if origin is TransformationSpec:
                    args = get_args(base)
                    if len(args) == 1 and _is_concrete_output(args[0]):
                        return args[0]
                type_args = get_args(base)
                if not isinstance(origin, type) or not type_args:
                    continue
                for parent in getattr(origin, "__orig_bases__", ()):
                    parent_origin = get_origin(parent) or parent
                    if parent_origin is not TransformationSpec:
                        continue
                    parent_args = get_args(parent)
                    if len(parent_args) != 1:
                        continue
                    output = parent_args[0]
                    if _is_concrete_output(output):
                        return output
                    specialized = type_args[0]
                    if _is_concrete_output(specialized):
                        return specialized
        raise ValueError(f"{cls.__name__} must specialize TransformationSpec[FeatureSpec]")

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
        if isinstance(value, TransformationSpec):
            return value
        if not isinstance(value, dict) or len(value) != 1:
            raise ValueError(f"step must be a single-key object, got {value!r}")
        (tag, wires), = value.items()
        spec_cls = TransformationSpec.REGISTRY.get(tag)
        if spec_cls is None:
            raise ValueError(f"unknown transformation {tag!r}")
        return spec_cls.structure(wires, spec_cls, None)

    @classmethod
    def unstructure_step(cls, inst: Self) -> dict[str, list[WireValue]]:
        return {type(inst).tag(): inst.unstructure()}

T = TypeVar("T", bound=TransformationSpec)

def register_transformation(name: str) -> Callable[[type[T]], type[T]]:
    def decorator(spec_cls: type[T]) -> type[T]:
        if not issubclass(spec_cls, TransformationSpec):
            raise TypeError(f"{spec_cls.__name__} must subclass TransformationSpec")
        if name in TransformationSpec.REGISTRY:
            raise ValueError(
                f"transformation {name!r} already registered as "
                f"{TransformationSpec.REGISTRY[name].__name__}"
            )
        TransformationSpec.REGISTRY[name] = spec_cls
        return spec_cls

    return decorator
