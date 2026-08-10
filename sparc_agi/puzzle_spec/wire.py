from typing import get_args, get_origin

from sparc_agi.puzzle_spec.features.base import FeatureSpec

WireValue = str | int | None

class WireRef[F: FeatureSpec]:
    @classmethod
    def spec_type(cls, typ: type) -> type[FeatureSpec] | None:
        origin = get_origin(typ)
        if origin is list:
            args = get_args(typ)
            if args:
                return cls.spec_type(args[0])
            return None
        origin = get_origin(typ) or typ
        if origin is not WireRef:
            return None
        args = get_args(typ)
        if len(args) == 1 and isinstance(args[0], type) and issubclass(args[0], FeatureSpec):
            return args[0]
        return FeatureSpec
