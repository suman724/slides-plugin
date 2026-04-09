"""Layer 3: Post-render layout validator with corrective fixes.

Audits every shape on every slide for formatting defects (overlaps,
out-of-bounds, text overflow), then applies up to 2 corrective passes
to fix issues mechanically.
"""

import math
from dataclasses import dataclass, field
from pptx.util import Inches, Pt, Emu


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOLERANCE = 0.1          # inches -- ignore deviations smaller than this
OVERLAP_H_THRESHOLD = 0.3  # inches -- horizontal overlap to flag
OVERLAP_V_THRESHOLD = 0.2  # inches -- vertical overlap to flag
MIN_FONT_PT = 8          # absolute floor for corrective font reduction
FOOTER_TOP_INCHES = 6.85  # 7.5 - 0.65 (footer reserved zone)
MAX_PASSES = 2


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ValidationIssue:
    slide_index: int
    shape_index: int
    issue_type: str          # "past_right", "past_bottom", "overlap", "text_overflow", etc.
    severity: str            # "error" or "warning"
    description: str
    auto_fixed: bool = False

    def __str__(self):
        status = "FIXED" if self.auto_fixed else self.severity.upper()
        return f"[{status}] Slide {self.slide_index + 1}, Shape {self.shape_index}: {self.description}"


# ---------------------------------------------------------------------------
# Shape analysis helpers
# ---------------------------------------------------------------------------

def _shape_bounds(shape):
    """Get shape bounds in inches."""
    return {
        "left": shape.left / 914400,
        "top": shape.top / 914400,
        "width": shape.width / 914400,
        "height": shape.height / 914400,
        "right": (shape.left + shape.width) / 914400,
        "bottom": (shape.top + shape.height) / 914400,
    }


def _shape_text(shape):
    """Get text content from shape, or empty string."""
    if shape.has_text_frame:
        return shape.text_frame.text.strip()
    return ""


def _shape_font_size(shape):
    """Get the first font size found in shape, or None."""
    if not shape.has_text_frame:
        return None
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            if run.font.size:
                return run.font.size.pt
    return None


def _estimate_text_height(text, width_inches, font_size_pt):
    """Estimate height needed for text in inches."""
    if not text or width_inches <= 0 or not font_size_pt or font_size_pt <= 0:
        return 0
    char_width = (font_size_pt * 0.55) / 72
    chars_per_line = max(1, int(width_inches / char_width))
    n_lines = max(1, math.ceil(len(text) / chars_per_line))
    line_height = (font_size_pt + 8) / 72
    return n_lines * line_height


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_slide(slide, slide_index, slide_width, slide_height):
    """Validate all shapes on a single slide. Returns list of ValidationIssue."""
    issues = []
    shapes_data = []

    for j, shape in enumerate(slide.shapes):
        bounds = _shape_bounds(shape)
        text = _shape_text(shape)
        font_size = _shape_font_size(shape)

        shapes_data.append({
            "index": j,
            "shape": shape,
            "bounds": bounds,
            "text": text,
            "font_size": font_size,
        })

        # Check: past right edge
        if bounds["right"] > slide_width + TOLERANCE:
            issues.append(ValidationIssue(
                slide_index, j, "past_right", "error",
                f"Shape extends past right edge ({bounds['right']:.2f}\" > {slide_width:.2f}\")"
            ))

        # Check: past bottom edge
        if bounds["bottom"] > slide_height + TOLERANCE:
            issues.append(ValidationIssue(
                slide_index, j, "past_bottom", "error",
                f"Shape extends past bottom ({bounds['bottom']:.2f}\" > {slide_height:.2f}\")"
            ))

        # Check: negative position
        if bounds["left"] < -TOLERANCE:
            issues.append(ValidationIssue(
                slide_index, j, "past_left", "error",
                f"Shape starts before left edge ({bounds['left']:.2f}\")"
            ))
        if bounds["top"] < -TOLERANCE:
            issues.append(ValidationIssue(
                slide_index, j, "past_top", "error",
                f"Shape starts before top edge ({bounds['top']:.2f}\")"
            ))

        # Check: text overflow
        if text and font_size and bounds["width"] > 0.2:
            est_height = _estimate_text_height(text, bounds["width"], font_size)
            if est_height > bounds["height"] * 1.5 and bounds["height"] > 0.05:
                issues.append(ValidationIssue(
                    slide_index, j, "text_overflow", "warning",
                    f"Text may overflow ({est_height:.2f}\" > {bounds['height']:.2f}\"): \"{text[:30]}...\""
                ))

        # Check: content in footer zone
        if text and bounds["bottom"] > FOOTER_TOP_INCHES and bounds["top"] < FOOTER_TOP_INCHES:
            # Only flag if the shape is primarily above the footer (content bleeding down)
            if bounds["top"] < FOOTER_TOP_INCHES - 0.5:
                issues.append(ValidationIssue(
                    slide_index, j, "in_footer_zone", "warning",
                    f"Content extends into footer zone (bottom={bounds['bottom']:.2f}\")"
                ))

    # Check: text shape overlaps
    text_shapes = [s for s in shapes_data if s["text"]]
    for a in range(len(text_shapes)):
        for b in range(a + 1, len(text_shapes)):
            sa = text_shapes[a]["bounds"]
            sb = text_shapes[b]["bounds"]

            h_overlap = min(sa["right"], sb["right"]) - max(sa["left"], sb["left"])
            v_overlap = min(sa["bottom"], sb["bottom"]) - max(sa["top"], sb["top"])

            if h_overlap > OVERLAP_H_THRESHOLD and v_overlap > OVERLAP_V_THRESHOLD:
                issues.append(ValidationIssue(
                    slide_index, text_shapes[a]["index"], "overlap", "error",
                    f"Overlaps with shape {text_shapes[b]['index']}: "
                    f"\"{text_shapes[a]['text'][:20]}\" vs \"{text_shapes[b]['text'][:20]}\""
                ))

    return issues, shapes_data


# ---------------------------------------------------------------------------
# Corrective fixes
# ---------------------------------------------------------------------------

def _fix_past_right(shape, slide_width):
    """Fix shape extending past right edge by reducing width."""
    bounds = _shape_bounds(shape)
    if bounds["right"] > slide_width + TOLERANCE:
        new_width = max(Inches(0.5), Inches(slide_width - bounds["left"] - 0.1))
        shape.width = new_width
        return True
    return False


def _fix_past_bottom(shape, slide_height):
    """Fix shape extending past bottom by reducing height."""
    bounds = _shape_bounds(shape)
    if bounds["bottom"] > slide_height + TOLERANCE:
        new_height = max(Inches(0.3), Inches(slide_height - bounds["top"] - 0.1))
        shape.height = new_height
        return True
    return False


def _fix_overlap(shape_above, shape_below):
    """Fix vertical overlap by shrinking the upper shape and/or reducing font.

    The 'above' shape is the one with the smaller top value.
    """
    bounds_a = _shape_bounds(shape_above)
    bounds_b = _shape_bounds(shape_below)

    # Determine which is actually above
    if bounds_a["top"] > bounds_b["top"]:
        shape_above, shape_below = shape_below, shape_above
        bounds_a, bounds_b = bounds_b, bounds_a

    gap = 0.05  # inches between shapes
    target_bottom = bounds_b["top"] - gap
    target_height = target_bottom - bounds_a["top"]

    if target_height < 0.1:
        return False

    # Try shrinking height first
    shape_above.height = Inches(target_height)

    # If upper shape has text that won't fit at the new height, reduce font
    text_a = _shape_text(shape_above)
    font_a = _shape_font_size(shape_above)
    if text_a and font_a:
        est = _estimate_text_height(text_a, bounds_a["width"], font_a)
        if est > target_height:
            # Reduce font until it fits
            _fix_text_overflow(shape_above)

    return True


def _fix_text_overflow(shape):
    """Fix text overflow by reducing font size.

    Does NOT expand shape height -- that risks causing overlaps with
    adjacent shapes. Font reduction is the safe fix.
    """
    if not shape.has_text_frame:
        return False

    bounds = _shape_bounds(shape)
    text = _shape_text(shape)

    if not text:
        return False

    fixed = False
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            if run.font.size and run.font.size.pt > MIN_FONT_PT:
                current = run.font.size.pt
                # Find the smallest size that fits the box
                for try_size in range(int(current) - 2, MIN_FONT_PT - 1, -2):
                    est = _estimate_text_height(text, bounds["width"], try_size)
                    if est <= bounds["height"] * 1.3:
                        run.font.size = Pt(try_size)
                        fixed = True
                        break
                else:
                    run.font.size = Pt(MIN_FONT_PT)
                    fixed = True
    return fixed


def _fix_in_footer_zone(shape):
    """Fix content extending into footer zone by reducing height."""
    bounds = _shape_bounds(shape)
    if bounds["bottom"] > FOOTER_TOP_INCHES and bounds["top"] < FOOTER_TOP_INCHES:
        new_height = FOOTER_TOP_INCHES - bounds["top"] - 0.05
        if new_height > 0.2:
            shape.height = Inches(new_height)
            return True
    return False


def _apply_fixes(slide, issues, shapes_data, slide_width, slide_height):
    """Apply corrective fixes to shapes for the given issues."""
    fixed_count = 0
    shape_map = {sd["index"]: sd["shape"] for sd in shapes_data}

    for issue in issues:
        if issue.auto_fixed:
            continue

        shape = shape_map.get(issue.shape_index)
        if shape is None:
            continue

        fixed = False

        if issue.issue_type in ("past_right", "past_left"):
            fixed = _fix_past_right(shape, slide_width)

        elif issue.issue_type in ("past_bottom", "past_top"):
            fixed = _fix_past_bottom(shape, slide_height)

        elif issue.issue_type == "overlap":
            # Parse the other shape index from description
            try:
                other_idx = int(issue.description.split("shape ")[1].split(":")[0])
                other_shape = shape_map.get(other_idx)
                if other_shape:
                    fixed = _fix_overlap(shape, other_shape)
            except (ValueError, IndexError):
                pass

        elif issue.issue_type == "text_overflow":
            fixed = _fix_text_overflow(shape)

        elif issue.issue_type == "in_footer_zone":
            fixed = _fix_in_footer_zone(shape)

        if fixed:
            issue.auto_fixed = True
            fixed_count += 1

    return fixed_count


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_presentation(prs):
    """Audit all slides for formatting defects.

    Returns:
        list of ValidationIssue
    """
    slide_width = prs.slide_width / 914400
    slide_height = prs.slide_height / 914400
    all_issues = []

    for i, slide in enumerate(prs.slides):
        issues, _ = _validate_slide(slide, i, slide_width, slide_height)
        all_issues.extend(issues)

    return all_issues


def validate_and_fix(prs, max_passes=MAX_PASSES):
    """Validate and apply corrective passes.

    Returns:
        (Presentation, list of all ValidationIssue including fixed ones)
    """
    slide_width = prs.slide_width / 914400
    slide_height = prs.slide_height / 914400
    all_issues = []

    for pass_num in range(max_passes):
        pass_had_fixes = False

        for i, slide in enumerate(prs.slides):
            issues, shapes_data = _validate_slide(slide, i, slide_width, slide_height)

            if issues:
                fixed_count = _apply_fixes(slide, issues, shapes_data, slide_width, slide_height)
                if fixed_count > 0:
                    pass_had_fixes = True

            all_issues.extend(issues)

        # If nothing was fixed this pass, further passes won't help
        if not pass_had_fixes:
            break

    # Final validation to see what remains
    final_issues = []
    for i, slide in enumerate(prs.slides):
        issues, _ = _validate_slide(slide, i, slide_width, slide_height)
        for issue in issues:
            issue.auto_fixed = False  # these are genuinely unresolved
            final_issues.append(issue)

    # Mark issues from earlier passes that are no longer present as fixed
    for prev in all_issues:
        still_present = any(
            f.slide_index == prev.slide_index
            and f.shape_index == prev.shape_index
            and f.issue_type == prev.issue_type
            for f in final_issues
        )
        if not still_present:
            prev.auto_fixed = True

    # Combine: fixed issues + remaining unresolved
    result = [i for i in all_issues if i.auto_fixed] + final_issues
    return prs, result
