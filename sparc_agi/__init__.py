"""sparc-agi: synthetic puzzle generation for ARC-AGI."""

from sparc_agi.parser import converter, load_source, structure_source
from sparc_agi.puzzle import (
    GeneratedPuzzle,
    Puzzle,
    PuzzleDescription,
    PuzzleSource,
    SampleCounts,
    SpecError,
    format_transformations,
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
    "converter",
    "format_transformations",
    "load_source",
    "structure_source",
    "validate_spec",
    "__version__",
]
