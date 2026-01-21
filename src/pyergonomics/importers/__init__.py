# This file makes the 'importers' directory a Python package.

from enum import Enum


class Unit(Enum):
    """Length units with conversion factor to meters."""
    M = 1.0
    CM = 0.01
    MM = 0.001
    INCH = 0.0254


from .bvh import from_bvh
from .video import init_from_video
from .zed import from_zed, BodyFormat
