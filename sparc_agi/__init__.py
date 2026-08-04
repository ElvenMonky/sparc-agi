"""Synthetic ARC-AGI puzzle generation."""

from sparc_agi.puzzle_spec.parser import converter, load_puzzle, structure_puzzle
from sparc_agi.puzzle_spec.puzzle import PuzzleSpec

__all__ = ["PuzzleSpec", "converter", "load_puzzle", "structure_puzzle"]
