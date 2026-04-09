"""Resolve style preferences from the style library into concrete values.

Loads style_library.json and resolves a metadata.style object into a
ResolvedStyle dataclass with all colors, fonts, and spacing as concrete
values ready for the renderer.
"""

import json
import os
from dataclasses import dataclass, field

from pptx.dml.color import RGBColor
from pptx.util import Pt


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIBRARY_PATH = os.path.join(SCRIPT_DIR, "style_library.json")

_cached_library = None


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FontRole:
    """Concrete font specification for a single role."""
    name: str
    size_pt: float
    bold: bool = False
    italic: bool = False

    @property
    def pt(self):
        return Pt(self.size_pt)


@dataclass
class ResolvedTypography:
    """Concrete typography hierarchy."""
    display: FontRole = field(default_factory=lambda: FontRole("Calibri", 36, bold=True))
    title: FontRole = field(default_factory=lambda: FontRole("Calibri", 28, bold=True))
    heading: FontRole = field(default_factory=lambda: FontRole("Calibri", 20, bold=True))
    body: FontRole = field(default_factory=lambda: FontRole("Calibri", 14))
    body_small: FontRole = field(default_factory=lambda: FontRole("Calibri", 12))
    caption: FontRole = field(default_factory=lambda: FontRole("Calibri", 10))
    metric: FontRole = field(default_factory=lambda: FontRole("Calibri", 40, bold=True))
    metric_label: FontRole = field(default_factory=lambda: FontRole("Calibri", 12))
    metric_delta: FontRole = field(default_factory=lambda: FontRole("Calibri", 14, bold=True))
    footer: FontRole = field(default_factory=lambda: FontRole("Calibri", 8))

    def get(self, role_name):
        """Get a FontRole by name string."""
        return getattr(self, role_name, self.body)


@dataclass
class ResolvedStyle:
    """Fully resolved style with concrete colors, fonts, and spacing."""
    # Palette
    palette_id: str = ""
    primary: RGBColor = field(default_factory=lambda: RGBColor(0x44, 0x54, 0x6A))
    secondary: RGBColor = field(default_factory=lambda: RGBColor(0x44, 0x72, 0xC4))
    accent: RGBColor = field(default_factory=lambda: RGBColor(0xED, 0x7D, 0x31))
    accent_alt: RGBColor = field(default_factory=lambda: RGBColor(0x3A, 0x8F, 0x6E))
    text_primary: RGBColor = field(default_factory=lambda: RGBColor(0x1A, 0x1A, 0x1A))
    text_secondary: RGBColor = field(default_factory=lambda: RGBColor(0x4A, 0x4A, 0x4A))
    text_on_dark: RGBColor = field(default_factory=lambda: RGBColor(0xFF, 0xFF, 0xFF))
    background: RGBColor = field(default_factory=lambda: RGBColor(0xFF, 0xFF, 0xFF))
    background_alt: RGBColor = field(default_factory=lambda: RGBColor(0xF0, 0xF4, 0xF8))
    positive: RGBColor = field(default_factory=lambda: RGBColor(0x2D, 0x8F, 0x5E))
    negative: RGBColor = field(default_factory=lambda: RGBColor(0xC0, 0x39, 0x2B))
    chart_colors: list = field(default_factory=list)
    gradient_pairs: list = field(default_factory=list)

    # Typography
    typography_id: str = ""
    typography: ResolvedTypography = field(default_factory=ResolvedTypography)

    # Spacing (proportional, 0.0-1.0)
    margin_left_pct: float = 0.056
    margin_right_pct: float = 0.056
    margin_top_pct: float = 0.053
    margin_bottom_pct: float = 0.08
    gutter_pct: float = 0.03

    # Slide dimensions
    slide_width_inches: float = 13.333
    slide_height_inches: float = 7.5

    @property
    def font_family(self):
        return self.typography.body.name


# ---------------------------------------------------------------------------
# Library loading
# ---------------------------------------------------------------------------

def load_library(path=None):
    """Load and cache the style library."""
    global _cached_library
    if _cached_library is not None:
        return _cached_library

    lib_path = path or LIBRARY_PATH
    if not os.path.exists(lib_path):
        # Return empty library -- fallbacks will handle it
        _cached_library = {
            "palettes": [],
            "typography_patterns": [],
            "discovered_patterns": [],
            "decorative_elements": {},
            "spacing_defaults": {},
        }
        return _cached_library

    with open(lib_path) as f:
        _cached_library = json.load(f)
    return _cached_library


def _hex_to_rgb(hex_str):
    """Convert hex color string to RGBColor."""
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ---------------------------------------------------------------------------
# Resolution logic
# ---------------------------------------------------------------------------

def _resolve_palette(library, style_prefs):
    """Resolve palette from style preferences.

    Checks: exact palette ID -> mood match -> first available -> defaults.
    """
    palettes = library.get("palettes", [])
    if not palettes:
        return {}

    # Exact ID match
    palette_id = style_prefs.get("palette", "")
    if palette_id:
        for p in palettes:
            if p["id"] == palette_id:
                return p

    # Mood match
    mood = style_prefs.get("mood", "")
    if mood:
        for p in palettes:
            if p.get("mood") == mood:
                return p

    # Default: first palette (highest source count, sorted by aggregator)
    return palettes[0]


def _resolve_typography(library, style_prefs):
    """Resolve typography pattern from style preferences."""
    patterns = library.get("typography_patterns", [])
    if not patterns:
        return {}

    # Exact ID match
    typo_id = style_prefs.get("typography", "")
    if typo_id:
        for t in patterns:
            if t["id"] == typo_id:
                return t

    # Font family match
    font = style_prefs.get("font", "")
    if font:
        for t in patterns:
            if t["font_family"].lower() == font.lower():
                return t

    # Default: first pattern (most sources)
    return patterns[0]


def _build_typography(typo_pattern):
    """Build ResolvedTypography from a typography pattern dict."""
    hierarchy = typo_pattern.get("hierarchy", {})
    font = typo_pattern.get("font_family", "Calibri")
    fallback = typo_pattern.get("fallback", "Arial")

    # Use primary font, fall back to system font if exotic
    # (Exotic fonts may not be installed; prefer safe defaults for body text)
    SAFE_FONTS = {"Calibri", "Arial", "Helvetica", "Segoe UI", "Verdana",
                  "Tahoma", "Trebuchet MS", "Georgia", "Times New Roman",
                  "Cambria", "Gill Sans MT"}
    body_font = font if font in SAFE_FONTS else fallback if fallback in SAFE_FONTS else "Calibri"
    heading_font = font  # headings can use the display font even if exotic

    # Size caps per role -- extracted sizes can be unrealistic
    SIZE_CAPS = {
        "display": 44, "title": 32, "heading": 24,
        "body": 16, "body_small": 14, "caption": 12,
        "metric": 48,
    }

    def _role(name, default_size, default_bold=False, use_body_font=False):  # noqa: E501
        h = hierarchy.get(name, {})
        raw_size = h.get("size_pt", default_size)
        capped_size = min(raw_size, SIZE_CAPS.get(name, 48))
        # If library says not bold but role normally is, keep the default
        is_bold = h.get("bold", default_bold) or default_bold
        return FontRole(
            name=body_font if use_body_font else heading_font,
            size_pt=capped_size,
            bold=is_bold,
        )

    return ResolvedTypography(
        display=_role("display", 36, default_bold=True),
        title=_role("title", 28, default_bold=True),
        heading=_role("heading", 20, default_bold=True),
        body=_role("body", 14, use_body_font=True),
        body_small=_role("body_small", 12, use_body_font=True),
        caption=_role("caption", 10, use_body_font=True),
        metric=_role("metric", 40, default_bold=True),
        metric_label=FontRole(body_font, 12),
        metric_delta=FontRole(body_font, 14, bold=True),
        footer=FontRole(body_font, 8),
    )


def resolve_style(metadata):
    """Resolve style from metadata into a ResolvedStyle.

    Args:
        metadata: dict with optional 'style' key containing palette/typography/mood prefs.

    Returns:
        ResolvedStyle with all colors, fonts, and spacing resolved.
    """
    library = load_library()
    style_prefs = metadata.get("style", {})

    # Resolve palette
    palette_data = _resolve_palette(library, style_prefs)
    colors = palette_data.get("colors", {})

    # Resolve typography
    typo_data = _resolve_typography(library, style_prefs)
    typography = _build_typography(typo_data) if typo_data else ResolvedTypography()

    # Resolve spacing
    spacing = library.get("spacing_defaults", {})

    # Build chart colors
    chart_hex = palette_data.get("chart_colors", [])
    chart_colors = [_hex_to_rgb(c) for c in chart_hex[:6]] if chart_hex else [
        _hex_to_rgb(colors.get("primary", "#44546A")),
        _hex_to_rgb(colors.get("accent", "#ED7D31")),
        _hex_to_rgb(colors.get("accent_alt", "#3A8F6E")),
        _hex_to_rgb(colors.get("secondary", "#4472C4")),
    ]

    # Build gradient pairs
    grad_hex = palette_data.get("gradient_pairs", [])
    gradient_pairs = [
        [_hex_to_rgb(g[0]), _hex_to_rgb(g[1])] for g in grad_hex if len(g) >= 2
    ]
    if not gradient_pairs:
        gradient_pairs = [[
            _hex_to_rgb(colors.get("primary", "#44546A")),
            _hex_to_rgb(colors.get("secondary", "#4472C4")),
        ]]

    return ResolvedStyle(
        palette_id=palette_data.get("id", "default"),
        primary=_hex_to_rgb(colors.get("primary", "#44546A")),
        secondary=_hex_to_rgb(colors.get("secondary", "#4472C4")),
        accent=_hex_to_rgb(colors.get("accent", "#ED7D31")),
        accent_alt=_hex_to_rgb(colors.get("accent_alt", "#3A8F6E")),
        text_primary=_hex_to_rgb(colors.get("text_primary", "#1A1A1A")),
        text_secondary=_hex_to_rgb(colors.get("text_secondary", "#4A4A4A")),
        text_on_dark=_hex_to_rgb(colors.get("text_on_dark", "#FFFFFF")),
        background=_hex_to_rgb(colors.get("background", "#FFFFFF")),
        background_alt=_hex_to_rgb(colors.get("background_alt", "#F0F4F8")),
        positive=_hex_to_rgb(colors.get("positive", "#2D8F5E")),
        negative=_hex_to_rgb(colors.get("negative", "#C0392B")),
        chart_colors=chart_colors,
        gradient_pairs=gradient_pairs,
        typography_id=typo_data.get("id", "default"),
        typography=typography,
        margin_left_pct=spacing.get("margin_left_pct", 0.056),
        margin_right_pct=spacing.get("margin_right_pct", 0.056),
        margin_top_pct=spacing.get("margin_top_pct", 0.053),
        margin_bottom_pct=spacing.get("margin_bottom_pct", 0.08),
        gutter_pct=spacing.get("typical_gutter_pct", 0.03),
    )
