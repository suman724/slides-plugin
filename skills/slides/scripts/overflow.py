"""Layer 1: Overflow prevention -- pre-render content/font/spacing adjustments.

Analyzes the semantic spec against layout zone sizes and applies preventive
adjustments before the layout engine renders shapes. Prevents issues that
are expensive or impossible to fix post-render.
"""

import math
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Font size floors (points)
MIN_BODY_PT = 10
MIN_SUBBULLET_PT = 9
MIN_HEADING_PT = 14
MIN_TITLE_PT = 20
MIN_CAPTION_PT = 8
MIN_METRIC_VALUE_PT = 24
MIN_TABLE_CELL_PT = 8

# Content quantity limits
MAX_BULLETS_PER_SLIDE = 8
HARD_MAX_BULLETS = 12
MAX_BULLETS_PER_COLUMN = 6
MAX_METRICS_PER_SLIDE = 4
MAX_METRICS_EXTENDED = 6
MAX_TIMELINE_MILESTONES = 6
MAX_TIMELINE_EXTENDED = 10
MAX_AGENDA_ITEMS = 7
MAX_TABLE_COLUMNS = 7
MAX_TABLE_ROWS = 12
MAX_CHART_CATEGORIES = 12
MAX_CHART_CATEGORIES_BAR = 15
MAX_TITLE_CHARS = 60
MAX_BULLET_CHARS = 140
MAX_COMPARE_OPTIONS = 2

# Spacing
DEFAULT_BULLET_SPACE_AFTER = 6
MIN_BULLET_SPACE_AFTER = 2


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class OverflowResult:
    adjusted_spec: dict = field(default_factory=dict)
    font_overrides: dict = field(default_factory=dict)
    spacing_overrides: dict = field(default_factory=dict)
    layout_upgrade: str = None
    warnings: list = field(default_factory=list)
    extra_slides: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Text estimation helpers
# ---------------------------------------------------------------------------

def _estimate_text_lines(text, width_inches, font_size_pt):
    """Estimate line count for text in a zone."""
    if not text or width_inches <= 0 or font_size_pt <= 0:
        return 1
    char_width_inches = (font_size_pt * 0.55) / 72
    chars_per_line = max(1, int(width_inches / char_width_inches))
    return max(1, math.ceil(len(text) / chars_per_line))


def _estimate_bullets_height(points, width_inches, body_pt=14, sub_pt=12,
                              space_after=6, space_before=2):
    """Estimate total height of bullet list in inches."""
    total = 0
    for point in points:
        if isinstance(point, str):
            text = point
            subpoints = []
        else:
            text = point.get("text", "")
            subpoints = point.get("subpoints", [])

        line_h = (body_pt + space_after + space_before) / 72
        n_lines = _estimate_text_lines(text, width_inches, body_pt)
        total += n_lines * line_h

        for sub in subpoints:
            sub_line_h = (sub_pt + 4 + 1) / 72
            sub_lines = _estimate_text_lines(sub, width_inches * 0.9, sub_pt)
            total += sub_lines * sub_line_h

    return total


# ---------------------------------------------------------------------------
# Per-scenario overflow handlers
# ---------------------------------------------------------------------------

def _handle_bullets(spec, zone_height, zone_width, result, slide_title):
    """Handle too many bullets or overly long bullet text."""
    points = spec.get("points", [])
    if not points:
        return

    n_points = len(points)
    body_pt = 14
    space_after = DEFAULT_BULLET_SPACE_AFTER

    # Strategy 1: Spacing reduction
    est_height = _estimate_bullets_height(points, zone_width, body_pt, space_after=space_after)
    if est_height > zone_height:
        space_after = MIN_BULLET_SPACE_AFTER
        result.spacing_overrides["bullet_space_after"] = space_after
        result.warnings.append(
            f"INFO: Reduced bullet spacing on '{slide_title}' ({n_points} items)"
        )

    # Strategy 2: Font reduction
    est_height = _estimate_bullets_height(points, zone_width, body_pt, space_after=space_after)
    if est_height > zone_height and body_pt > MIN_BODY_PT:
        body_pt = max(MIN_BODY_PT, body_pt - 2)
        result.font_overrides["body"] = body_pt
        result.font_overrides["body_small"] = max(MIN_SUBBULLET_PT, body_pt - 1)
        result.warnings.append(
            f"INFO: Reduced body font to {body_pt}pt on '{slide_title}'"
        )

    # Strategy 3: Content splitting
    if n_points > HARD_MAX_BULLETS:
        import copy
        mid = n_points // 2
        extra_slide = copy.deepcopy(spec)
        spec["points"] = points[:mid]
        extra_slide["points"] = points[mid:]
        extra_slide["title"] = f"{slide_title} (continued)"
        result.extra_slides.append(extra_slide)
        result.warnings.append(
            f"WARNING: Split '{slide_title}' into 2 slides ({n_points} bullets)"
        )

    # Check individual bullet text length
    for i, point in enumerate(points):
        text = point.get("text", point) if isinstance(point, dict) else str(point)
        if len(text) > MAX_BULLET_CHARS:
            if isinstance(point, dict):
                point["text"] = text[:MAX_BULLET_CHARS - 3] + "..."
            else:
                spec["points"][i] = text[:MAX_BULLET_CHARS - 3] + "..."
            result.warnings.append(
                f"WARNING: Truncated bullet {i+1} on '{slide_title}' at {MAX_BULLET_CHARS} chars"
            )


def _handle_title(spec, zone_width, result):
    """Handle overly long title."""
    title = spec.get("title", "")
    if not title:
        return

    title_pt = 28
    lines = _estimate_text_lines(title, zone_width, title_pt)

    if lines > 2:
        # Try reducing font
        for pt in range(26, MIN_TITLE_PT - 1, -2):
            if _estimate_text_lines(title, zone_width, pt) <= 2:
                result.font_overrides["title"] = pt
                result.warnings.append(
                    f"INFO: Reduced title font to {pt}pt ({len(title)} chars)"
                )
                return

        # Truncate as last resort
        char_width = (MIN_TITLE_PT * 0.55) / 72
        max_chars = int(zone_width / char_width) * 2  # 2 lines
        spec["title"] = title[:max_chars - 3] + "..."
        result.font_overrides["title"] = MIN_TITLE_PT
        result.warnings.append(
            f"WARNING: Truncated title at {max_chars} chars"
        )


def _handle_metrics(spec, zone_width, result, slide_title):
    """Handle too many metric cards."""
    metrics = spec.get("metrics", [])
    n = len(metrics)

    if n <= MAX_METRICS_PER_SLIDE:
        return

    if n <= MAX_METRICS_EXTENDED:
        # 5-6 metrics: use 2-row grid
        result.layout_upgrade = "grid_2row"
        result.font_overrides["metric"] = 30
        result.warnings.append(
            f"INFO: Switched to 2-row grid on '{slide_title}' ({n} metrics)"
        )
    else:
        # 7+: split into slides of 4
        import copy
        spec["metrics"] = metrics[:MAX_METRICS_PER_SLIDE]
        remaining = metrics[MAX_METRICS_PER_SLIDE:]
        while remaining:
            chunk = remaining[:MAX_METRICS_PER_SLIDE]
            remaining = remaining[MAX_METRICS_PER_SLIDE:]
            extra = copy.deepcopy(spec)
            extra["metrics"] = chunk
            extra["title"] = f"{slide_title} (continued)"
            result.extra_slides.append(extra)
        result.warnings.append(
            f"WARNING: Split '{slide_title}' into {1 + len(result.extra_slides)} slides ({n} metrics)"
        )


def _handle_table(spec, zone_width, zone_height, result, slide_title):
    """Handle tables that are too wide or too tall."""
    columns = spec.get("columns", [])
    rows = spec.get("rows", [])
    n_cols = len(columns)
    n_rows = len(rows)

    # Too wide
    if n_cols > MAX_TABLE_COLUMNS:
        result.font_overrides["table_cell"] = MIN_TABLE_CELL_PT
        result.warnings.append(
            f"INFO: Reduced table cell font on '{slide_title}' ({n_cols} columns)"
        )

    # Too tall -- split
    if n_rows > MAX_TABLE_ROWS:
        import copy
        spec["rows"] = rows[:MAX_TABLE_ROWS]
        remaining = rows[MAX_TABLE_ROWS:]
        while remaining:
            chunk = remaining[:MAX_TABLE_ROWS]
            remaining = remaining[MAX_TABLE_ROWS:]
            extra = copy.deepcopy(spec)
            extra["rows"] = chunk
            extra["title"] = f"{slide_title} (continued)"
            result.extra_slides.append(extra)
        result.warnings.append(
            f"WARNING: Split '{slide_title}' table into {1 + len(result.extra_slides)} slides ({n_rows} rows)"
        )


def _handle_timeline(spec, result, slide_title):
    """Handle too many timeline milestones."""
    steps = spec.get("steps", [])
    n = len(steps)

    if n <= MAX_TIMELINE_MILESTONES:
        return

    if n <= MAX_TIMELINE_EXTENDED:
        # Compress labels
        result.font_overrides["timeline_label"] = 10
        result.font_overrides["timeline_detail"] = 8
        result.warnings.append(
            f"INFO: Compressed timeline labels on '{slide_title}' ({n} milestones)"
        )
    else:
        # Split into 2 timelines
        import copy
        mid = n // 2
        extra = copy.deepcopy(spec)
        spec["steps"] = steps[:mid]
        extra["steps"] = steps[mid:]
        extra["title"] = f"{slide_title} (continued)"
        result.extra_slides.append(extra)
        result.warnings.append(
            f"WARNING: Split '{slide_title}' timeline into 2 slides ({n} milestones)"
        )


def _handle_compare(spec, result, slide_title):
    """Handle compare/evaluate with too many options.

    Note: 3 sides/options is normal for categorize -- only split at 4+.
    The intent mapper upgrades compare with 3+ sides to categorize,
    so by the time we get here, categorize with 3 is expected.
    """
    import copy

    # Compare / Categorize -- split at 4+ sides
    sides = spec.get("sides", [])
    if len(sides) > 3:
        spec["sides"] = sides[:3]
        for i in range(3, len(sides), 3):
            extra = copy.deepcopy(spec)
            extra["sides"] = sides[i:i+3]
            extra["title"] = f"{slide_title} (continued)"
            result.extra_slides.append(extra)
        result.warnings.append(
            f"WARNING: Split '{slide_title}' comparison into {1 + len(result.extra_slides)} slides"
        )

    # Evaluate -- split at 3+ options
    options = spec.get("options", [])
    if len(options) > 3:
        spec["options"] = options[:2]
        for i in range(2, len(options), 2):
            extra = copy.deepcopy(spec)
            extra["options"] = options[i:i+2]
            extra["title"] = f"{slide_title} (continued)"
            result.extra_slides.append(extra)
        result.warnings.append(
            f"WARNING: Split '{slide_title}' evaluation into {1 + len(result.extra_slides)} slides"
        )


def _handle_agenda(spec, zone_height, result, slide_title):
    """Handle too many agenda/outline items."""
    items = spec.get("items", [])
    n = len(items)

    if n <= MAX_AGENDA_ITEMS:
        return

    if n <= 10:
        # Compress: reduce item spacing, drop subtexts
        result.spacing_overrides["item_height"] = 0.50
        for item in items:
            if isinstance(item, dict):
                item.pop("detail", None)
                item.pop("subtext", None)
        result.warnings.append(
            f"INFO: Compressed agenda on '{slide_title}' ({n} items, dropped subtexts)"
        )
    else:
        # Split into 2 slides
        import copy
        mid = n // 2
        extra = copy.deepcopy(spec)
        spec["items"] = items[:mid]
        extra["items"] = items[mid:]
        extra["title"] = f"{slide_title} (continued)"
        result.extra_slides.append(extra)
        result.warnings.append(
            f"WARNING: Split '{slide_title}' agenda into 2 slides ({n} items)"
        )


def _handle_chart(spec, result, slide_title):
    """Handle charts with too many categories."""
    chart = spec.get("chart", {})
    categories = chart.get("categories", [])
    chart_type = chart.get("type", "column_clustered")
    n = len(categories)

    max_cats = MAX_CHART_CATEGORIES_BAR if "bar" in chart_type else MAX_CHART_CATEGORIES

    if n <= max_cats:
        return

    # Strategy: switch column to bar (handles more categories)
    if "column" in chart_type and n <= MAX_CHART_CATEGORIES_BAR:
        chart["type"] = chart_type.replace("column", "bar")
        result.warnings.append(
            f"INFO: Switched chart to bar on '{slide_title}' ({n} categories)"
        )
    elif n > MAX_CHART_CATEGORIES_BAR:
        # Truncate categories
        for series in chart.get("series", []):
            series["values"] = series["values"][:MAX_CHART_CATEGORIES_BAR]
        chart["categories"] = categories[:MAX_CHART_CATEGORIES_BAR]
        result.warnings.append(
            f"WARNING: Truncated chart to {MAX_CHART_CATEGORIES_BAR} categories on '{slide_title}'"
        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def apply_overflow_rules(slide_spec, layout_pattern, resolved_style):
    """Analyze content against zone capacity and return preventive adjustments.

    Args:
        slide_spec: dict -- the semantic slide specification
        layout_pattern: dict -- the resolved layout pattern with zones
        resolved_style: ResolvedStyle -- resolved typography/spacing

    Returns:
        OverflowResult with adjustments, extra slides, and warnings.
    """
    result = OverflowResult(adjusted_spec=slide_spec)
    intent = slide_spec.get("intent", "explain")
    title = slide_spec.get("title", f"Slide")

    # Compute zone dimensions in inches
    sw = resolved_style.slide_width_inches
    sh = resolved_style.slide_height_inches
    FOOTER_RESERVED = 0.65

    content_zone = None
    title_zone = None
    for zone in layout_pattern.get("zones", []):
        if zone["role"] == "content":
            content_zone = zone
        elif zone["role"] == "title":
            title_zone = zone

    # Content zone dimensions (with expansion, matching layout_engine logic)
    if content_zone:
        b = content_zone["bounds_pct"]
        zone_width = max(b["width"] * sw, sw * 0.85)
        zone_top = b["top"] * sh
        max_bottom = sh - FOOTER_RESERVED
        zone_height = max(max_bottom - zone_top, 4.0)
    else:
        zone_width = sw * 0.85
        zone_height = 5.0

    # Title zone width
    title_width = sw * 0.85
    if title_zone:
        title_width = title_zone["bounds_pct"]["width"] * sw

    # --- Apply handlers based on intent ---

    _handle_title(slide_spec, title_width, result)

    if intent in ("explain", "outline", "summarize"):
        if intent == "outline":
            _handle_agenda(slide_spec, zone_height, result, title)
        elif intent == "summarize":
            # Takeaways are similar to bullets
            takeaways = slide_spec.get("takeaways", [])
            if takeaways:
                temp_spec = {"points": [{"text": t} for t in takeaways], "title": title}
                _handle_bullets(temp_spec, zone_height, zone_width, result, title)
                slide_spec["takeaways"] = [p["text"] for p in temp_spec["points"]]
                result.extra_slides = [
                    {**e, "takeaways": [p["text"] for p in e.get("points", [])]}
                    for e in result.extra_slides
                ]
        else:
            _handle_bullets(slide_spec, zone_height, zone_width, result, title)

    elif intent == "measure":
        _handle_metrics(slide_spec, zone_width, result, title)

    elif intent == "tabulate":
        _handle_table(slide_spec, zone_width, zone_height, result, title)

    elif intent == "visualize":
        _handle_chart(slide_spec, result, title)

    elif intent == "sequence":
        _handle_timeline(slide_spec, result, title)

    elif intent in ("compare", "evaluate", "categorize"):
        _handle_compare(slide_spec, result, title)

    result.adjusted_spec = slide_spec
    return result
