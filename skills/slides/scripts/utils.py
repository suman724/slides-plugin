"""Geometry math, text fitting, and color utility functions."""

from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor


def inches(val):
    """Convert float inches to EMU."""
    return Inches(val)


def pt(val):
    """Convert float points to EMU."""
    return Pt(val)


def hex_to_rgb(hex_str):
    """Convert hex color string (#RRGGBB or RRGGBB) to RGBColor."""
    hex_str = hex_str.lstrip('#')
    return RGBColor(
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16),
    )


def lighten_color(color, factor=0.3):
    """Lighten an RGBColor by mixing with white. Factor 0-1."""
    r = int(color[0] + (255 - color[0]) * factor)
    g = int(color[1] + (255 - color[1]) * factor)
    b = int(color[2] + (255 - color[2]) * factor)
    return RGBColor(min(r, 255), min(g, 255), min(b, 255))


def darken_color(color, factor=0.3):
    """Darken an RGBColor by mixing with black. Factor 0-1."""
    r = int(color[0] * (1 - factor))
    g = int(color[1] * (1 - factor))
    b = int(color[2] * (1 - factor))
    return RGBColor(max(r, 0), max(g, 0), max(b, 0))


def with_alpha(color, alpha):
    """Return a tuple (RGBColor, alpha_int) for use with transparency.

    alpha: 0.0 (fully transparent) to 1.0 (fully opaque)
    python-pptx doesn't natively support alpha on all elements,
    but this helper pairs color + alpha for XML manipulation if needed.
    """
    return (color, int(alpha * 100000))


def clamp(value, min_val, max_val):
    """Clamp a numeric value between min and max."""
    return max(min_val, min(value, max_val))


def emu_to_inches(emu_val):
    """Convert EMU to inches (float)."""
    return emu_val / 914400


def inches_to_emu(inches_val):
    """Convert inches (float) to EMU."""
    return int(inches_val * 914400)
