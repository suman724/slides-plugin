"""Generic layout engine that renders slides from semantic content + layout patterns.

Takes a layout pattern (proportional zones), content mapping, and resolved style,
then renders everything into positioned shapes on a slide.
"""

from pptx.enum.text import PP_ALIGN

from shape_renderer import (
    render_solid_bg, render_gradient_bg,
    render_title, render_subtitle, render_text,
    render_accent_bar, render_panel,
    render_bullets, render_columns, render_metrics,
    render_chart, render_table,
    render_timeline, render_emphasis, render_evaluation,
    render_numbered_items, render_takeaway,
    render_footer,
)


def render_slide(slide, intent, layout_pattern, content_mapping, style, metadata,
                 page_num, total_pages):
    """Render a complete slide from layout pattern + content mapping.

    Args:
        slide: pptx slide object (blank layout)
        intent: the resolved semantic intent string
        layout_pattern: dict with zones, background_type, decorative
        content_mapping: dict mapping zone roles to content data
        style: ResolvedStyle
        metadata: presentation metadata dict
        page_num: current slide number
        total_pages: total slide count
    """
    sw = style.slide_width_inches
    sh = style.slide_height_inches

    # 1. Render background
    _render_background(slide, layout_pattern, style, sw, sh)

    # 2. Render each zone
    zones = layout_pattern.get("zones", [])
    # Roles that need expanded height
    EXPANDABLE_ROLES = {"content", "table", "chart", "media"}

    for zone in zones:
        role = zone["role"]
        if role in EXPANDABLE_ROLES:
            bounds = _content_bounds(zone["bounds_pct"], sw, sh)
        else:
            bounds = _to_inches(zone["bounds_pct"], sw, sh)
        content = content_mapping.get(role)

        if content is None:
            continue

        _render_zone(slide, role, bounds, content, intent, style)

    # 3. Render decorative elements
    _render_decorative(slide, layout_pattern, style, sw, sh)

    # 4. Render footer (skip for opening/closing/section_break)
    if intent not in ("open", "close", "divide"):
        render_footer(slide, metadata, page_num, total_pages, style)


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

def _render_background(slide, layout_pattern, style, sw, sh):
    """Apply solid or gradient background."""
    bg_type = layout_pattern.get("background_type", "solid")

    if bg_type == "gradient" and style.gradient_pairs:
        pair = style.gradient_pairs[0]
        render_gradient_bg(slide, pair[0], pair[1], sw, sh)
    elif bg_type == "gradient":
        render_gradient_bg(slide, style.primary, style.secondary, sw, sh)
    # solid backgrounds use the default white -- no explicit fill needed


# ---------------------------------------------------------------------------
# Zone rendering dispatch
# ---------------------------------------------------------------------------

def _render_zone(slide, role, bounds, content, intent, style):
    """Dispatch zone rendering based on role and content type."""
    left, top, width, height = bounds

    # --- Title zone ---
    if role == "title":
        text = content if isinstance(content, str) else str(content)
        if intent in ("open", "close"):
            # Cover/closing: larger, centered, on-dark
            render_text(
                slide, text, left, top, width, height,
                style.typography.display, style.text_on_dark,
                alignment=PP_ALIGN.CENTER if intent == "close" else PP_ALIGN.LEFT,
            )
        elif intent == "divide":
            # Section divider: title on the right side
            render_text(
                slide, text, left, top, width, height,
                style.typography.display, style.text_primary,
            )
            render_accent_bar(slide, left, top + height + 0.05, min(2.0, width * 0.3), style)
        else:
            render_title(slide, text, bounds, style)

    # --- Subtitle zone ---
    elif role == "subtitle":
        text = content if isinstance(content, str) else str(content)
        if intent in ("open", "close"):
            render_text(
                slide, text, left, top, width, height,
                style.typography.body, style.text_on_dark,
                alignment=PP_ALIGN.CENTER if intent == "close" else PP_ALIGN.LEFT,
            )
        else:
            render_subtitle(slide, text, bounds, style)

    # --- Contact zone ---
    elif role == "contact":
        text = content if isinstance(content, str) else str(content)
        render_text(
            slide, text, left, top, width, height,
            style.typography.body, style.text_on_dark,
            alignment=PP_ALIGN.CENTER,
        )

    # --- Panel zone (section divider colored block) ---
    elif role == "panel":
        render_panel(slide, left, top, width, height, style.primary)

    # --- Number zone (section number) ---
    elif role == "number":
        text = str(content).zfill(2) if content else ""
        if text:
            from style_resolver import FontRole
            render_text(
                slide, text, left, top, width, height,
                FontRole(style.typography.display.name, 60, bold=True),
                style.text_on_dark,
                alignment=PP_ALIGN.CENTER,
            )

    # --- Content zone (the main workhorse) ---
    elif role == "content":
        _render_content_zone(slide, content, left, top, width, height, intent, style)

    # --- Dedicated table zone ---
    elif role == "table":
        if isinstance(content, dict):
            render_table(slide, content, left, top, width, height, style)

    # --- Dedicated chart zone ---
    elif role == "chart":
        if isinstance(content, dict):
            render_chart(slide, content, left, top, width, height, style)

    # --- Media zone ---
    elif role == "media":
        _render_media(slide, content, left, top, width, height, style)

    # --- Annotation zone ---
    elif role == "annotation":
        text = content if isinstance(content, str) else str(content)
        render_text(
            slide, text, left, top, width, height,
            style.typography.caption, style.text_secondary,
        )

    # --- Footer zone (handled separately) ---
    elif role == "footer":
        pass  # Footer rendered by render_footer() call in render_slide()


# ---------------------------------------------------------------------------
# Content zone rendering (dispatches by content type)
# ---------------------------------------------------------------------------

def _render_content_zone(slide, content, left, top, width, height, intent, style):
    """Render content into a content zone based on content type."""
    if not isinstance(content, dict):
        # Plain text fallback
        render_text(
            slide, str(content), left, top, width, height,
            style.typography.body, style.text_primary,
        )
        return

    content_type = content.get("type", "text")

    if content_type == "bullets":
        data = content.get("data", [])
        render_bullets(slide, data, left + 0.10, top, width - 0.20, height, style)

    elif content_type == "columns":
        data = content.get("data", [])
        render_columns(slide, data, left, top, width, height, style)

    elif content_type == "metrics":
        data = content.get("data", [])
        render_metrics(slide, data, left, top, width, height, style)

    elif content_type == "chart":
        data = content.get("data", {})
        render_chart(slide, data, left, top, width, height, style)

    elif content_type == "table":
        render_table(slide, content, left, top, width, height, style)

    elif content_type == "evaluation":
        data = content.get("data", [])
        render_evaluation(slide, data, left, top, width, height, style)

    elif content_type == "timeline":
        data = content.get("data", [])
        render_timeline(slide, data, left, top, width, height, style)

    elif content_type == "emphasis":
        data = content.get("data", {})
        render_emphasis(slide, data, left, top, width, height, style)

    elif content_type == "numbered_items":
        data = content.get("data", [])
        render_numbered_items(slide, data, left, top, width, height, style)

    elif content_type == "takeaway":
        render_takeaway(slide, content, left, top, width, height, style)

    else:
        # Generic text
        text = content.get("data", "")
        if isinstance(text, str):
            render_text(
                slide, text, left, top, width, height,
                style.typography.body, style.text_primary,
            )


# ---------------------------------------------------------------------------
# Media rendering
# ---------------------------------------------------------------------------

def _render_media(slide, content, left, top, width, height, style):
    """Render media (image or placeholder)."""
    from pptx.util import Inches
    from pptx.enum.shapes import MSO_SHAPE

    image_path = content if isinstance(content, str) else ""
    if image_path:
        try:
            slide.shapes.add_picture(
                image_path, Inches(left), Inches(top), Inches(width), Inches(height),
            )
            return
        except Exception:
            pass

    # Placeholder
    from shape_renderer import render_rounded_card
    render_rounded_card(slide, left, top, width, height, style.background_alt)
    render_text(
        slide, "[Image]",
        left, top + height / 2 - 0.25, width, 0.50,
        style.typography.body, style.text_secondary,
        alignment=PP_ALIGN.CENTER,
    )


# ---------------------------------------------------------------------------
# Decorative elements
# ---------------------------------------------------------------------------

def _render_decorative(slide, layout_pattern, style, sw, sh):
    """Render decorative elements specified by the layout pattern."""
    decorative = layout_pattern.get("decorative", [])
    for dec_type in decorative:
        if dec_type == "accent_bar":
            # Add accent bar below the title zone (if title exists)
            title_zone = next(
                (z for z in layout_pattern["zones"] if z["role"] == "title"), None
            )
            if title_zone:
                b = title_zone["bounds_pct"]
                bar_left = b["left"] * sw
                bar_top = (b["top"] + b["height"]) * sh + 0.05
                render_accent_bar(slide, bar_left, bar_top, 1.5, style)

        elif dec_type == "vertical_stripe":
            render_panel(slide, 0.45 * sw, 0.24 * sh, 0.008 * sw, 0.47 * sh, style.accent)

        # Other decorative types can be added as discovered


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _to_inches(bounds_pct, slide_w, slide_h):
    """Convert proportional bounds to (left, top, width, height) inches.

    Clamps content so it doesn't extend into the footer zone (bottom 0.65")
    or past the slide edges.
    """
    FOOTER_RESERVED = 0.65  # inches reserved at bottom for footer
    MIN_MARGIN = 0.5        # minimum left/right margin

    left = max(bounds_pct["left"] * slide_w, 0)
    top = max(bounds_pct["top"] * slide_h, 0)
    width = bounds_pct["width"] * slide_w
    height = bounds_pct["height"] * slide_h

    # Clamp right edge to slide width minus margin
    if left + width > slide_w - MIN_MARGIN:
        width = slide_w - MIN_MARGIN - left

    # Clamp bottom edge to above footer zone
    max_bottom = slide_h - FOOTER_RESERVED
    if top + height > max_bottom:
        height = max(0.5, max_bottom - top)

    # Ensure minimum content width
    if width < 2.0:
        left = MIN_MARGIN
        width = slide_w - 2 * MIN_MARGIN

    return (left, top, width, height)


def _content_bounds(bounds_pct, slide_w, slide_h):
    """Convert proportional bounds for content zones with height expansion.

    Content zones (bullets, charts, tables, etc.) need enough vertical space
    to render. If the discovered zone is too short, expand it to fill the
    available space above the footer.
    """
    left, top, width, height = _to_inches(bounds_pct, slide_w, slide_h)

    MIN_CONTENT_HEIGHT = 4.0
    FOOTER_RESERVED = 0.65
    max_bottom = slide_h - FOOTER_RESERVED
    available_height = max_bottom - top

    if height < MIN_CONTENT_HEIGHT and available_height > MIN_CONTENT_HEIGHT:
        height = available_height

    return (left, top, width, height)
