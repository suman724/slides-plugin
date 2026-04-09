"""Design system: themes, grid, typography, and decorative element specifications."""

from dataclasses import dataclass, field
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

@dataclass
class Grid:
    """Positioning grid for 16:9 widescreen slides (13.333" x 7.5")."""

    slide_width: float = 13.333
    slide_height: float = 7.5
    margin_left: float = 0.75
    margin_right: float = 0.75
    margin_top: float = 0.40
    margin_bottom: float = 0.60
    title_height: float = 0.80
    footer_height: float = 0.35
    gutter: float = 0.40

    @property
    def content_width(self):
        return self.slide_width - self.margin_left - self.margin_right

    @property
    def content_top(self):
        return self.margin_top + self.title_height + 0.20

    @property
    def content_bottom(self):
        return self.slide_height - self.margin_bottom - self.footer_height

    @property
    def content_height(self):
        return self.content_bottom - self.content_top

    def col_width(self, n_cols):
        """Width of each column when content area is split into n_cols."""
        return (self.content_width - (n_cols - 1) * self.gutter) / n_cols

    def col_left(self, col_index, n_cols):
        """Left position of the col_index-th column (0-based)."""
        w = self.col_width(n_cols)
        return self.margin_left + col_index * (w + self.gutter)


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

@dataclass
class FontSpec:
    """Specification for a single font role."""
    name: str
    size: int        # in points
    bold: bool = False
    italic: bool = False

    @property
    def pt(self):
        return Pt(self.size)


@dataclass
class Typography:
    """Full typography hierarchy."""
    slide_title: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 28, bold=True))
    section_title: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 36, bold=True))
    heading: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 20, bold=True))
    body: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 14))
    body_small: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 12))
    caption: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 10))
    metric_value: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 40, bold=True))
    metric_label: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 12))
    metric_delta: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 14, bold=True))
    footer: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 8))
    title_slide_title: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 36, bold=True))
    title_slide_subtitle: FontSpec = field(default_factory=lambda: FontSpec("Calibri", 18))


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

@dataclass
class Theme:
    """Complete visual theme for presentations."""
    name: str
    primary: RGBColor
    secondary: RGBColor
    accent: RGBColor
    accent_alt: RGBColor
    text_primary: RGBColor
    text_secondary: RGBColor
    text_on_primary: RGBColor
    background: RGBColor
    background_alt: RGBColor
    positive: RGBColor
    negative: RGBColor
    chart_palette: list
    typography: Typography = field(default_factory=Typography)

    @property
    def font_family(self):
        return self.typography.slide_title.name


# ---------------------------------------------------------------------------
# Theme Definitions
# ---------------------------------------------------------------------------

CORPORATE_BLUE = Theme(
    name="corporate_blue",
    primary=RGBColor(0x1B, 0x3A, 0x6B),       # navy
    secondary=RGBColor(0x2E, 0x5C, 0x9E),      # medium blue
    accent=RGBColor(0xE8, 0x91, 0x3A),          # amber
    accent_alt=RGBColor(0x3A, 0x8F, 0x6E),      # green
    text_primary=RGBColor(0x1A, 0x1A, 0x1A),    # near-black
    text_secondary=RGBColor(0x4A, 0x4A, 0x4A),  # dark gray
    text_on_primary=RGBColor(0xFF, 0xFF, 0xFF),  # white
    background=RGBColor(0xFF, 0xFF, 0xFF),       # white
    background_alt=RGBColor(0xF0, 0xF4, 0xF8),  # light blue-gray
    positive=RGBColor(0x2D, 0x8F, 0x5E),        # green
    negative=RGBColor(0xC0, 0x39, 0x2B),         # red
    chart_palette=[
        RGBColor(0x1B, 0x3A, 0x6B),
        RGBColor(0xE8, 0x91, 0x3A),
        RGBColor(0x3A, 0x8F, 0x6E),
        RGBColor(0x2E, 0x5C, 0x9E),
        RGBColor(0xC0, 0x39, 0x2B),
        RGBColor(0x6C, 0x5B, 0x7B),
    ],
)

MODERN_DARK = Theme(
    name="modern_dark",
    primary=RGBColor(0x1A, 0x1A, 0x2E),         # near-black
    secondary=RGBColor(0x16, 0x21, 0x3E),        # dark navy
    accent=RGBColor(0xE9, 0x45, 0x60),           # coral red
    accent_alt=RGBColor(0x0F, 0x34, 0x60),       # deep blue
    text_primary=RGBColor(0xE8, 0xE8, 0xE8),     # light gray
    text_secondary=RGBColor(0xA0, 0xA0, 0xA0),   # medium gray
    text_on_primary=RGBColor(0xFF, 0xFF, 0xFF),   # white
    background=RGBColor(0x0F, 0x0F, 0x23),        # deep dark
    background_alt=RGBColor(0x1A, 0x1A, 0x2E),    # slightly lighter
    positive=RGBColor(0x4C, 0xAF, 0x50),          # green
    negative=RGBColor(0xE9, 0x45, 0x60),          # coral red
    chart_palette=[
        RGBColor(0xE9, 0x45, 0x60),
        RGBColor(0x4C, 0xAF, 0x50),
        RGBColor(0x29, 0xB6, 0xF6),
        RGBColor(0xFF, 0xCA, 0x28),
        RGBColor(0xAB, 0x47, 0xBC),
        RGBColor(0x26, 0xA6, 0x9A),
    ],
)

MINIMAL = Theme(
    name="minimal",
    primary=RGBColor(0xFF, 0xFF, 0xFF),          # white
    secondary=RGBColor(0xF5, 0xF5, 0xF5),        # light gray
    accent=RGBColor(0x00, 0x66, 0xCC),            # blue
    accent_alt=RGBColor(0x2D, 0x2D, 0x2D),        # charcoal
    text_primary=RGBColor(0x1A, 0x1A, 0x1A),      # near-black
    text_secondary=RGBColor(0x6B, 0x6B, 0x6B),    # medium gray
    text_on_primary=RGBColor(0x1A, 0x1A, 0x1A),   # near-black (since bg is white)
    background=RGBColor(0xFF, 0xFF, 0xFF),         # white
    background_alt=RGBColor(0xFA, 0xFA, 0xFA),     # near-white
    positive=RGBColor(0x2D, 0x8F, 0x5E),           # green
    negative=RGBColor(0xC0, 0x39, 0x2B),            # red
    chart_palette=[
        RGBColor(0x00, 0x66, 0xCC),
        RGBColor(0x2D, 0x2D, 0x2D),
        RGBColor(0x2D, 0x8F, 0x5E),
        RGBColor(0xE8, 0x91, 0x3A),
        RGBColor(0xC0, 0x39, 0x2B),
        RGBColor(0x6C, 0x5B, 0x7B),
    ],
)


# ---------------------------------------------------------------------------
# Theme Registry
# ---------------------------------------------------------------------------

THEMES = {
    "corporate_blue": CORPORATE_BLUE,
    "modern_dark": MODERN_DARK,
    "minimal": MINIMAL,
}


def load_theme(name: str) -> Theme:
    """Load a theme by name. Defaults to corporate_blue if not found."""
    return THEMES.get(name, CORPORATE_BLUE)
