"""sparc-agi: synthetic puzzle generation for ARC-AGI."""

from sparc_agi.puzzle import (
    GeneratedPuzzle,
    Puzzle,
    PuzzleDescription,
    PuzzleSource,
    SampleCounts,
    SpecError,
    format_transformations,
    load_source,
    validate_spec,
)

__version__ = "0.1.0"
__all__ = [
    "GeneratedPuzzle",
    "Puzzle",
    "PuzzleDescription",
    "PuzzleSource",
    "SampleCounts",
    "SpecError",
    "format_transformations",
    "load_source",
    "validate_spec",
    "__version__",
]
