"""Transformation registry.

Skeleton steps in the bible are single-key tagged objects whose payload is the
input wire list (or, later, a dict of fields)::

    { "Rotate": ["a", 0] }
    { "ArrangeObjects": ["b", 0, 1] }

Wire refs are cache keys (``str``) or sample ports (``int``): ``0`` is the
puzzle input, ``1..n`` are prior skeleton step outputs.

Each transformation declares feature *families* for its slots via
``input_features`` / ``output_feature``. Kinds within a family
(``object.sprite``, …) are interchangeable. If ``input_variadic`` is true,
the last declared family may repeat for extra trailing wires.

Register a new transformation with ``@register_transformation("Name")``.
"""

from dataclasses import dataclass, field
from typing import Callable, ClassVar, TypeVar

WireRef = str | int

T = TypeVar("T", bound="Transformation")

TRANSFORMATION_REGISTRY: dict[str, type[Transformation]] = {}


@dataclass
class Transformation:
    """Base class for all registered transformation steps."""

    inputs: list[WireRef] = field(default_factory=list)

    __transformation_name__: ClassVar[str]
    # Feature families expected per positional input slot.
    input_features: ClassVar[tuple[str, ...]] = ()
    # If True, len(inputs) may exceed len(input_features); extras use the last family.
    input_variadic: ClassVar[bool] = False
    # Feature family produced by this step.
    output_feature: ClassVar[str] = ""

    @classmethod
    def expected_input_family(cls, slot: int) -> str:
        """Feature family expected at input slot ``slot`` (0-based)."""
        n = len(cls.input_features)
        if n == 0:
            raise ValueError(f"{cls.__name__} declares no input_features")
        if slot < n:
            return cls.input_features[slot]
        if cls.input_variadic:
            return cls.input_features[-1]
        raise IndexError(f"{cls.__name__} has no input slot {slot}")

    @classmethod
    def check_arity(cls, n_inputs: int) -> None:
        n = len(cls.input_features)
        if cls.input_variadic:
            if n_inputs < n:
                raise ValueError(
                    f"{cls.__transformation_name__} expects at least {n} input(s), got {n_inputs}"
                )
        elif n_inputs != n:
            raise ValueError(
                f"{cls.__transformation_name__} expects {n} input(s), got {n_inputs}"
            )


def register_transformation(name: str) -> Callable[[type[T]], type[T]]:
    """Register a Transformation subclass under a bible tag name."""

    def decorator(cls: type[T]) -> type[T]:
        if not issubclass(cls, Transformation):
            raise TypeError(f"{cls.__name__} must subclass Transformation")
        if name in TRANSFORMATION_REGISTRY:
            raise ValueError(
                f"transformation {name!r} already registered as {TRANSFORMATION_REGISTRY[name].__name__}"
            )
        if not cls.input_features:
            raise TypeError(f"{cls.__name__} must declare input_features")
        if not cls.output_feature:
            raise TypeError(f"{cls.__name__} must declare output_feature")
        cls.__transformation_name__ = name
        TRANSFORMATION_REGISTRY[name] = cls
        return cls

    return decorator
