"""sparc-agi: synthetic puzzle generation for ARC-AGI."""

from sparc_agi.puzzle_spec import PuzzleSpec, PuzzleSpecBible, SpecError, load_bible, validate_spec

__version__ = "0.1.0"
__all__ = [
    "PuzzleSpec",
    "PuzzleSpecBible",
    "SpecError",
    "load_bible",
    "validate_spec",
    "__version__",
]

