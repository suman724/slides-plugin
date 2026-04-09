"""Reusable slide-element building functions.

Every component takes (slide, ..., theme, grid) and never hardcodes
colors or positions -- all visual decisions come from the theme and grid.
"""

from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import math

from design_system import Theme, Grid, FontSpec


# ---------------------------------------------------------------------------
# Background components
# ---------------------------------------------------------------------------

def add_solid_bg(slide, color):
    """Fill the entire slide background with a solid color."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_gradient_bg(slide, color1, color2):
    """Fill the slide background with a two-stop gradient (top-left to bottom-right).

    Note: python-pptx has limited gradient support on backgrounds.
    We simulate with a full-slide rectangle shape.
    """
    grid = Grid()
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(0),
        Inches(grid.slide_width), Inches(grid.slide_height),
    )
    shape.line.fill.background()  # no border

    fill = shape.fill
    fill.gradient()
    fill.gradient_stops[0].color.rgb = color1
    fill.gradient_stops[0].position = 0.0
    fill.gradient_stops[1].color.rgb = color2
    fill.gradient_stops[1].position = 1.0

    # Send to back so other elements render on top
    sp = shape._element
    sp.getparent().remove(sp)
    slide.shapes._spTree.insert(2, sp)


def add_shape_bg(slide, left, top, width, height, color):
    """Add a colored rectangle at a specific position (e.g., for a band or stripe)."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top),
        Inches(width), Inches(height),
    )
    shape.line.fill.background()
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = color
    return shape


# ---------------------------------------------------------------------------
# Text components
# ---------------------------------------------------------------------------

def _apply_font(run, font_spec, color=None):
    """Apply a FontSpec and optional color to a run."""
    run.font.name = font_spec.name
    run.font.size = font_spec.pt
    run.font.bold = font_spec.bold
    run.font.italic = font_spec.italic
    if color:
        run.font.color.rgb = color


def add_text_box(slide, text, left, top, width, height, font_spec, color=None,
                 alignment=PP_ALIGN.LEFT, word_wrap=True):
    """Add a styled text box at a specific position."""
    txbox = slide.shapes.add_textbox(
        Inches(left), Inches(top),
        Inches(width), Inches(height),
    )
    tf = txbox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = alignment
    run = p.add_run()
    run.text = text
    _apply_font(run, font_spec, color)
    return txbox


def add_slide_title(slide, text, theme, grid):
    """Add the standard slide title with an accent bar underneath."""
    # Title text
    txbox = add_text_box(
        slide, text,
        left=grid.margin_left,
        top=grid.margin_top,
        width=grid.content_width,
        height=grid.title_height,
        font_spec=theme.typography.slide_title,
        color=theme.text_primary,
    )
    tf = txbox.text_frame
    tf.vertical_anchor = MSO_ANCHOR.BOTTOM

    # Accent bar
    add_accent_bar(
        slide,
        left=grid.margin_left,
        top=grid.margin_top + grid.title_height + 0.05,
        width=1.5,
        theme=theme,
    )
    return txbox


def add_slide_footer(slide, metadata, page_num, total_pages, theme, grid):
    """Add footer bar with separator line, company name, and page number."""
    footer_top = grid.slide_height - grid.margin_bottom

    # Separator line
    add_separator_line(
        slide,
        left=grid.margin_left,
        top=footer_top - 0.05,
        width=grid.content_width,
        theme=theme,
    )

    # Left: company name
    company = metadata.get("company", "")
    if company:
        add_text_box(
            slide, company,
            left=grid.margin_left,
            top=footer_top,
            width=3.0,
            height=grid.footer_height,
            font_spec=theme.typography.footer,
            color=theme.text_secondary,
        )

    # Center: confidentiality
    confidentiality = metadata.get("confidentiality", "")
    if confidentiality:
        add_text_box(
            slide, confidentiality,
            left=grid.margin_left + grid.content_width / 2 - 1.5,
            top=footer_top,
            width=3.0,
            height=grid.footer_height,
            font_spec=theme.typography.footer,
            color=theme.text_secondary,
            alignment=PP_ALIGN.CENTER,
        )

    # Right: page number
    add_text_box(
        slide, f"{page_num} / {total_pages}",
        left=grid.margin_left + grid.content_width - 2.0,
        top=footer_top,
        width=2.0,
        height=grid.footer_height,
        font_spec=theme.typography.footer,
        color=theme.text_secondary,
        alignment=PP_ALIGN.RIGHT,
    )


# ---------------------------------------------------------------------------
# Decorative components
# ---------------------------------------------------------------------------

def add_accent_bar(slide, left, top, width, theme, height=0.04):
    """Add a thin colored accent bar (default 4px visual height)."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top),
        Inches(width), Inches(height),
    )
    shape.line.fill.background()
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = theme.accent
    return shape


def add_separator_line(slide, left, top, width, theme, weight=0.5):
    """Add a thin horizontal separator line."""
    from pptx.util import Pt as PtUtil
    line_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top),
        Inches(width), PtUtil(weight),
    )
    line_shape.line.fill.background()
    fill = line_shape.fill
    fill.solid()
    fill.fore_color.rgb = theme.text_secondary
    return line_shape


def add_rounded_card(slide, left, top, width, height, fill_color, border_color=None):
    """Add a rounded rectangle card with optional border."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top),
        Inches(width), Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


# ---------------------------------------------------------------------------
# Bullet list component
# ---------------------------------------------------------------------------

def add_bullet_list(slide, body_items, left, top, width, height, theme, grid):
    """Add a formatted bullet list from body items.

    body_items: list of dicts with keys: type, text, level (0 or 1)
    """
    txbox = slide.shapes.add_textbox(
        Inches(left), Inches(top),
        Inches(width), Inches(height),
    )
    tf = txbox.text_frame
    tf.word_wrap = True

    for i, item in enumerate(body_items):
        level = item.get("level", 0)
        text = item.get("text", "")

        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        p.level = level
        p.space_after = Pt(6)
        p.space_before = Pt(2)

        # Bullet character
        bullet_char = "\u2022"  # bullet dot
        if level == 1:
            bullet_char = "\u2013"  # en-dash for sub-bullets
            p.space_after = Pt(4)

        run = p.add_run()
        run.text = f"{bullet_char}  {text}"

        font_spec = theme.typography.body if level == 0 else theme.typography.body_small
        color = theme.text_primary if level == 0 else theme.text_secondary
        _apply_font(run, font_spec, color)

    return txbox


# ---------------------------------------------------------------------------
# Metric / KPI components
# ---------------------------------------------------------------------------

def add_metric_card(slide, metric, left, top, width, height, theme):
    """Add a KPI metric card with value, label, and delta.

    metric: dict with keys: label, value, delta, direction (up/down)
    """
    # Card background
    add_rounded_card(slide, left, top, width, height, theme.background_alt)

    # Value (large number)
    add_text_box(
        slide, metric["value"],
        left=left + 0.15,
        top=top + 0.25,
        width=width - 0.30,
        height=0.70,
        font_spec=theme.typography.metric_value,
        color=theme.text_primary,
        alignment=PP_ALIGN.CENTER,
    )

    # Label
    add_text_box(
        slide, metric["label"],
        left=left + 0.15,
        top=top + 0.95,
        width=width - 0.30,
        height=0.35,
        font_spec=theme.typography.metric_label,
        color=theme.text_secondary,
        alignment=PP_ALIGN.CENTER,
    )

    # Delta with direction arrow
    delta_text = metric.get("delta", "")
    direction = metric.get("direction", "up")
    if delta_text:
        arrow = "\u25B2" if direction == "up" else "\u25BC"  # up/down triangle
        delta_color = theme.positive if direction == "up" else theme.negative
        add_text_box(
            slide, f"{arrow} {delta_text}",
            left=left + 0.15,
            top=top + 1.30,
            width=width - 0.30,
            height=0.30,
            font_spec=theme.typography.metric_delta,
            color=delta_color,
            alignment=PP_ALIGN.CENTER,
        )


def add_arrow_indicator(slide, direction, left, top, theme, size=0.20):
    """Add an up or down arrow indicator."""
    arrow = "\u25B2" if direction == "up" else "\u25BC"
    color = theme.positive if direction == "up" else theme.negative
    add_text_box(
        slide, arrow,
        left=left, top=top,
        width=size, height=size,
        font_spec=FontSpec("Calibri", 14, bold=True),
        color=color,
        alignment=PP_ALIGN.CENTER,
    )


# ---------------------------------------------------------------------------
# Numbered item component (for agenda, takeaway)
# ---------------------------------------------------------------------------

def add_numbered_item(slide, number, text, subtext, left, top, width, height, theme):
    """Add a numbered item with circle marker, main text, and optional subtext."""
    circle_size = 0.45
    text_left = left + circle_size + 0.20

    # Number circle
    circle = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(left), Inches(top + 0.05),
        Inches(circle_size), Inches(circle_size),
    )
    circle.fill.solid()
    circle.fill.fore_color.rgb = theme.accent
    circle.line.fill.background()

    # Number text in circle
    tf = circle.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = str(number)
    _apply_font(run, FontSpec("Calibri", 14, bold=True), theme.text_on_primary)

    # Main text
    add_text_box(
        slide, text,
        left=text_left,
        top=top,
        width=width - circle_size - 0.20,
        height=0.35,
        font_spec=theme.typography.heading,
        color=theme.text_primary,
    )

    # Subtext
    if subtext:
        add_text_box(
            slide, subtext,
            left=text_left,
            top=top + 0.35,
            width=width - circle_size - 0.20,
            height=0.30,
            font_spec=theme.typography.body_small,
            color=theme.text_secondary,
        )


# ---------------------------------------------------------------------------
# Timeline component
# ---------------------------------------------------------------------------

def add_timeline_marker(slide, milestone, center_x, top, theme, is_first=False, is_last=False):
    """Add a timeline milestone with circle, date label, and detail text."""
    circle_size = 0.30
    # Circle marker
    circle = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(center_x - circle_size / 2), Inches(top),
        Inches(circle_size), Inches(circle_size),
    )
    circle.fill.solid()
    circle.fill.fore_color.rgb = theme.accent
    circle.line.fill.background()

    # Date label (above)
    add_text_box(
        slide, milestone["date"],
        left=center_x - 0.75,
        top=top - 0.50,
        width=1.5,
        height=0.35,
        font_spec=theme.typography.body_small,
        color=theme.accent,
        alignment=PP_ALIGN.CENTER,
    )

    # Title (below)
    add_text_box(
        slide, milestone["label"],
        left=center_x - 0.9,
        top=top + circle_size + 0.10,
        width=1.8,
        height=0.35,
        font_spec=FontSpec("Calibri", 12, bold=True),
        color=theme.text_primary,
        alignment=PP_ALIGN.CENTER,
    )

    # Detail (further below)
    detail = milestone.get("detail", "")
    if detail:
        add_text_box(
            slide, detail,
            left=center_x - 0.9,
            top=top + circle_size + 0.45,
            width=1.8,
            height=0.50,
            font_spec=theme.typography.caption,
            color=theme.text_secondary,
            alignment=PP_ALIGN.CENTER,
        )


# ---------------------------------------------------------------------------
# Pro/Con list component
# ---------------------------------------------------------------------------

def add_pro_con_list(slide, items, is_pro, left, top, width, theme):
    """Add a list of items prefixed with check/cross marks."""
    txbox = slide.shapes.add_textbox(
        Inches(left), Inches(top),
        Inches(width), Inches(len(items) * 0.35 + 0.1),
    )
    tf = txbox.text_frame
    tf.word_wrap = True

    prefix = "\u2713" if is_pro else "\u2717"  # check / cross
    color = theme.positive if is_pro else theme.negative

    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(4)

        # Prefix run (colored)
        prefix_run = p.add_run()
        prefix_run.text = f"{prefix}  "
        _apply_font(prefix_run, theme.typography.body, color)

        # Text run
        text_run = p.add_run()
        text_run.text = item
        _apply_font(text_run, theme.typography.body, theme.text_primary)
