from dataclasses import dataclass, fields
from typing import Any, Callable, ClassVar, Self, TypeVar, get_origin

WireRef = str | int | None

@dataclass
class TransformationSpec:
    REGISTRY: ClassVar[dict[str, type[Self]]] = {}

    @classmethod
    def tag(cls) -> str:
        for name, registered in TransformationSpec.REGISTRY.items():
            if registered is cls:
                return name
        raise ValueError(f"{cls.__name__} is not registered")

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
            raise ValueError(
                f"{cls.__name__} expects {len(dc_fields)} wires, got {len(wires)!r}"
            )
        return cls(*wires)

    def unstructure(self) -> list[WireRef]:
        dc_fields = fields(self)
        if dc_fields and get_origin(dc_fields[-1].type) is list:
            wires = [getattr(self, dc_field.name) for dc_field in dc_fields[:-1]]
            wires.extend(getattr(self, dc_fields[-1].name))
            return wires
        return [getattr(self, dc_field.name) for dc_field in dc_fields]

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
    def unstructure_step(cls, inst: Self) -> dict[str, list[WireRef]]:
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
