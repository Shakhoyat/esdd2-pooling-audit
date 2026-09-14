"""Recompute every numeric claim in the paper from per-clip scores.

Nothing here reads a cached result. Every function takes scores and labels and
returns a number, so a reader can check a claim without trusting our records.
"""
__version__ = "1.0.0"
