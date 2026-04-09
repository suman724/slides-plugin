#!/usr/bin/env python3
"""Extract design patterns from a PPTX file into a JSON style profile.

Analyzes colors, typography, layouts, spacing, decorative elements, and backgrounds.

Usage:
    python3 extract.py pipeline/raw/sc-aurora.pptx
    python3 extract.py --all               # extract all files in raw/
    python3 extract.py --all --output-dir pipeline/profiles/
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE

try:
    from lxml import etree
except ImportError:
    etree = None


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "raw")
PROFILES_DIR = os.path.join(SCRIPT_DIR, "profiles")


# ---------------------------------------------------------------------------
# Theme font resolution
# ---------------------------------------------------------------------------

def _resolve_theme_fonts(prs):
    """Extract the actual font names for theme placeholders (+mn-lt, +mj-lt).

    PowerPoint themes define 'major' and 'minor' Latin fonts. When python-pptx
    returns None or '+mn-lt'/'+mj-lt', the actual font is in the theme XML.
    """
    result = {"major": None, "minor": None}
    if etree is None:
        return result

    try:
        slide_master = prs.slide_masters[0]
        theme_part = None
        for rel in slide_master.part.rels.values():
            if "theme" in rel.reltype:
                theme_part = rel.target_part
                break

        if theme_part is None:
            return result

        tree = etree.fromstring(theme_part.blob)
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

        major_font = tree.find(".//a:majorFont/a:latin", ns)
        if major_font is not None:
            result["major"] = major_font.get("typeface")

        minor_font = tree.find(".//a:minorFont/a:latin", ns)
        if minor_font is not None:
            result["minor"] = minor_font.get("typeface")
    except Exception:
        pass

    return result


def _resolve_font_name(name, theme_fonts):
    """Resolve a font name, replacing theme placeholders with actual names."""
    if name is None or name == "Unknown":
        # Default to theme minor font (body text)
        return theme_fonts.get("minor") or theme_fonts.get("major") or "Calibri"
    if name == "+mn-lt" or name == "+mn-ea" or name == "+mn-cs":
        return theme_fonts.get("minor") or "Calibri"
    if name == "+mj-lt" or name == "+mj-ea" or name == "+mj-cs":
        return theme_fonts.get("major") or "Calibri"
    return name


# ---------------------------------------------------------------------------
# Color extraction
# ---------------------------------------------------------------------------

def _rgb_to_hex(rgb):
    """Convert RGBColor or tuple to hex string."""
    if isinstance(rgb, RGBColor):
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    if isinstance(rgb, (tuple, list)) and len(rgb) == 3:
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    return str(rgb)


def _safe_get_fill_color(shape):
    """Safely extract fill color from a shape."""
    try:
        fill = shape.fill
        if fill.type is not None and fill.type == 1:  # MSO_FILL.SOLID
            return _rgb_to_hex(fill.fore_color.rgb)
    except Exception:
        pass
    return None


def _safe_get_line_color(shape):
    """Safely extract line color from a shape."""
    try:
        line = shape.line
        if line.fill.type is not None and line.fill.type == 1:
            return _rgb_to_hex(line.color.rgb)
    except Exception:
        pass
    return None


def _safe_get_font_color(run):
    """Safely extract font color from a text run."""
    try:
        if run.font.color and run.font.color.type is not None:
            return _rgb_to_hex(run.font.color.rgb)
    except Exception:
        pass
    return None


def extract_theme_colors(prs):
    """Extract theme colors from the presentation's theme XML."""
    theme_colors = {}
    if etree is None:
        return theme_colors

    try:
        # Access the slide master's theme
        slide_master = prs.slide_masters[0]
        theme_part = None

        # Navigate relationships to find the theme
        for rel in slide_master.part.rels.values():
            if "theme" in rel.reltype:
                theme_part = rel.target_part
                break

        if theme_part is None:
            return theme_colors

        # Parse theme XML
        tree = etree.fromstring(theme_part.blob)
        ns = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        }

        # Look for color scheme elements
        color_scheme = tree.find(".//a:clrScheme", ns)
        if color_scheme is not None:
            color_slots = ["dk1", "lt1", "dk2", "lt2",
                          "accent1", "accent2", "accent3", "accent4",
                          "accent5", "accent6", "hlink", "folHlink"]
            for slot in color_slots:
                elem = color_scheme.find(f"a:{slot}", ns)
                if elem is not None:
                    # Can be srgbClr or sysClr
                    srgb = elem.find("a:srgbClr", ns)
                    if srgb is not None:
                        theme_colors[slot] = f"#{srgb.get('val', '000000')}"
                    else:
                        sys_clr = elem.find("a:sysClr", ns)
                        if sys_clr is not None:
                            last_clr = sys_clr.get("lastClr", "000000")
                            theme_colors[slot] = f"#{last_clr}"
    except Exception:
        pass

    return theme_colors


def extract_colors(prs):
    """Extract all colors used in the presentation."""
    fill_colors = Counter()
    text_colors = Counter()
    line_colors = Counter()
    gradient_stops = []

    for slide in prs.slides:
        for shape in slide.shapes:
            # Fill colors
            fc = _safe_get_fill_color(shape)
            if fc:
                fill_colors[fc] += 1

            # Gradient fills
            try:
                fill = shape.fill
                if fill.type is not None and fill.type == 2:  # GRADIENT
                    stops = []
                    for stop in fill.gradient_stops:
                        stops.append(_rgb_to_hex(stop.color.rgb))
                    if stops:
                        gradient_stops.append(stops)
            except Exception:
                pass

            # Line colors
            lc = _safe_get_line_color(shape)
            if lc:
                line_colors[lc] += 1

            # Text colors
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        tc = _safe_get_font_color(run)
                        if tc:
                            text_colors[tc] += 1

        # Slide background
        try:
            bg = slide.background
            fill = bg.fill
            if fill.type is not None and fill.type == 1:
                fc = _rgb_to_hex(fill.fore_color.rgb)
                fill_colors[fc] += 1
            elif fill.type is not None and fill.type == 2:
                stops = []
                for stop in fill.gradient_stops:
                    stops.append(_rgb_to_hex(stop.color.rgb))
                if stops:
                    gradient_stops.append(stops)
        except Exception:
            pass

    theme_colors = extract_theme_colors(prs)

    return {
        "theme_colors": theme_colors,
        "sampled_fills": [c for c, _ in fill_colors.most_common(15)],
        "sampled_text_colors": [c for c, _ in text_colors.most_common(10)],
        "sampled_line_colors": [c for c, _ in line_colors.most_common(5)],
        "gradient_stops": gradient_stops[:10],  # cap at 10 unique gradients
        "fill_frequency": dict(fill_colors.most_common(20)),
        "text_frequency": dict(text_colors.most_common(10)),
    }


# ---------------------------------------------------------------------------
# Typography extraction
# ---------------------------------------------------------------------------

def extract_typography(prs, theme_fonts=None):
    """Extract font usage patterns."""
    if theme_fonts is None:
        theme_fonts = _resolve_theme_fonts(prs)

    font_counter = Counter()  # (name, size_pt, bold) -> count
    font_names = Counter()
    size_distribution = defaultdict(lambda: {"bold": 0, "regular": 0, "samples": []})

    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    name = _resolve_font_name(run.font.name, theme_fonts)
                    size = None
                    if run.font.size:
                        size = round(run.font.size.pt, 1)
                    bold = bool(run.font.bold)

                    font_names[name] += 1
                    if size:
                        key = (name, size, bold)
                        font_counter[key] += 1

                        weight = "bold" if bold else "regular"
                        size_distribution[size][weight] += 1
                        if len(size_distribution[size]["samples"]) < 3:
                            sample = run.text.strip()[:50]
                            if sample:
                                size_distribution[size]["samples"].append(sample)

    # Infer hierarchy roles
    hierarchy = _infer_typography_hierarchy(font_counter)

    return {
        "fonts_used": [{"name": n, "frequency": c} for n, c in font_names.most_common(5)],
        "size_distribution": [
            {
                "size_pt": size,
                "bold_count": data["bold"],
                "regular_count": data["regular"],
                "samples": data["samples"],
            }
            for size, data in sorted(size_distribution.items(), reverse=True)
        ],
        "hierarchy": hierarchy,
    }


def _infer_typography_hierarchy(font_counter):
    """Classify font sizes into display/heading/body/caption roles."""
    # Group by size, sum counts
    size_totals = defaultdict(int)
    size_bold = defaultdict(int)
    size_font = defaultdict(str)

    for (name, size, bold), count in font_counter.items():
        size_totals[size] += count
        if bold:
            size_bold[size] += count
        # Track most common font per size
        if not size_font[size] or count > font_counter.get((size_font[size], size, bold), 0):
            size_font[size] = name

    if not size_totals:
        return {}

    sorted_sizes = sorted(size_totals.keys(), reverse=True)

    hierarchy = {}
    for size in sorted_sizes:
        is_mostly_bold = size_bold[size] > size_totals[size] * 0.5
        font = size_font[size]

        if size >= 30 and "display" not in hierarchy:
            hierarchy["display"] = {"font": font, "size_pt": size, "bold": is_mostly_bold}
        elif size >= 22 and "title" not in hierarchy:
            hierarchy["title"] = {"font": font, "size_pt": size, "bold": is_mostly_bold}
        elif size >= 16 and "heading" not in hierarchy:
            hierarchy["heading"] = {"font": font, "size_pt": size, "bold": is_mostly_bold}
        elif 11 <= size <= 15 and "body" not in hierarchy:
            # Pick the size with highest count in this range
            body_candidates = [(s, size_totals[s]) for s in sorted_sizes if 11 <= s <= 15]
            if body_candidates:
                best_size = max(body_candidates, key=lambda x: x[1])[0]
                hierarchy["body"] = {"font": size_font[best_size], "size_pt": best_size, "bold": False}
        elif size <= 10 and "caption" not in hierarchy:
            hierarchy["caption"] = {"font": font, "size_pt": size, "bold": False}

    return hierarchy


# ---------------------------------------------------------------------------
# Layout extraction
# ---------------------------------------------------------------------------

def _emu_to_pct(value, total):
    """Convert EMU to proportion of total."""
    if total == 0:
        return 0.0
    return round(value / total, 4)


def _classify_zone_role(bounds_pct, shape, slide_shapes_count):
    """Heuristic: classify a shape's zone role based on position, size, and content."""
    top = bounds_pct["top"]
    left = bounds_pct["left"]
    height = bounds_pct["height"]
    width = bounds_pct["width"]
    area = width * height

    # Chart -- check first, charts can be anywhere
    if shape.shape_type == MSO_SHAPE_TYPE.CHART:
        return "chart"

    # Table
    if shape.has_table:
        return "table"

    # Image/picture -- only meaningful if reasonably sized
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        if area > 0.03:  # at least 3% of slide area (not a tiny icon)
            return "media"
        else:
            return "decorative"  # tiny icon/thumbnail

    # Group shapes containing pictures are media only if large enough
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP and area > 0.05:
        return "media"

    # Decorative: very thin shapes (accent bars, lines, stripes)
    if height < 0.02 or width < 0.02:
        return "decorative"

    # Decorative: full-width bands used as backgrounds
    if width > 0.9 and height < 0.15 and not shape.has_text_frame:
        return "decorative"

    # Decorative: small shapes without text (icons, circles, rectangles)
    if area < 0.02 and not (shape.has_text_frame and shape.text_frame.text.strip()):
        return "decorative"

    # Footer zone: bottom 12% of slide
    if top > 0.88:
        return "footer"

    # Title zone: top 22% of slide, reasonably wide, short text
    if top < 0.22 and width > 0.4 and shape.has_text_frame:
        text = shape.text_frame.text.strip()
        if text and len(text) < 120:
            # Check if it looks like a title (large font or short text)
            font_size = None
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.size:
                        font_size = run.font.size.pt
                        break
                if font_size:
                    break
            # Large font or short text in top area = title
            if font_size and font_size >= 18:
                return "title"
            if len(text) < 60:
                return "title"

    # Subtitle: just below title area, wide, short text
    if 0.15 < top < 0.35 and width > 0.4 and shape.has_text_frame:
        text = shape.text_frame.text.strip()
        if text and len(text) < 80:
            font_size = None
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.size:
                        font_size = run.font.size.pt
                        break
                if font_size:
                    break
            if font_size and 12 <= font_size <= 20:
                return "subtitle"

    # Content: medium-to-large text areas
    if shape.has_text_frame and shape.text_frame.text.strip():
        text = shape.text_frame.text.strip()
        # Needs reasonable size to be content (not a tiny label)
        if area > 0.04 and (height > 0.1 or len(text) > 30):
            return "content"

    # Non-text shapes of reasonable size (placeholders, colored blocks)
    if area > 0.05:
        return "content"

    # Small non-text shape = decorative
    return "decorative"


def extract_layouts(prs):
    """Extract layout patterns from all slides."""
    slide_width = prs.slide_width
    slide_height = prs.slide_height
    layouts = []

    for slide_idx, slide in enumerate(prs.slides):
        zones = []
        decorative_shapes = []

        # Detect background type
        bg_type = "solid"
        bg_colors = []
        try:
            fill = slide.background.fill
            if fill.type is not None and fill.type == 2:  # gradient
                bg_type = "gradient"
                for stop in fill.gradient_stops:
                    bg_colors.append(_rgb_to_hex(stop.color.rgb))
            elif fill.type is not None and fill.type == 1:  # solid
                bg_colors.append(_rgb_to_hex(fill.fore_color.rgb))
        except Exception:
            pass

        for shape in slide.shapes:
            bounds_pct = {
                "left": _emu_to_pct(shape.left, slide_width),
                "top": _emu_to_pct(shape.top, slide_height),
                "width": _emu_to_pct(shape.width, slide_width),
                "height": _emu_to_pct(shape.height, slide_height),
            }

            role = _classify_zone_role(bounds_pct, shape, len(slide.shapes))

            if role == "decorative":
                fill_color = _safe_get_fill_color(shape)
                decorative_shapes.append({
                    "bounds_pct": bounds_pct,
                    "fill": fill_color,
                    "inferred_type": _infer_decorative_type(bounds_pct),
                })
            else:
                text_sample = ""
                font_size = None
                if shape.has_text_frame and shape.text_frame.text.strip():
                    text_sample = shape.text_frame.text.strip()[:60]
                    for para in shape.text_frame.paragraphs:
                        for run in para.runs:
                            if run.font.size:
                                font_size = round(run.font.size.pt, 1)
                                break
                        if font_size:
                            break

                zones.append({
                    "role": role,
                    "bounds_pct": bounds_pct,
                    "text_sample": text_sample,
                    "font_size_pt": font_size,
                })

        # Detect column structure (needed by purpose classifier)
        n_cols = _detect_columns(zones)

        # Infer slide purpose
        purpose = _infer_slide_purpose(zones, bg_type, slide_idx, len(prs.slides), n_cols)

        layouts.append({
            "slide_index": slide_idx,
            "inferred_purpose": purpose,
            "n_columns": n_cols,
            "background": {"type": bg_type, "colors": bg_colors},
            "zones": zones,
            "decorative_shapes": decorative_shapes,
        })

    return layouts


def _infer_decorative_type(bounds_pct):
    """Classify decorative shapes by geometry."""
    w = bounds_pct["width"]
    h = bounds_pct["height"]

    if h < 0.01 and w > 0.05:
        return "accent_bar"
    if w < 0.015 and h > 0.1:
        return "vertical_stripe"
    if w > 0.9 and h < 0.15:
        return "horizontal_band"
    if abs(w - h) < 0.01 and w < 0.06:
        return "circle_marker"
    return "shape"


def _infer_slide_purpose(zones, bg_type, slide_idx, total_slides, n_cols):
    """Heuristic slide purpose classification.

    Uses zone roles, background type, position in deck, and column count
    to infer the semantic purpose of a slide.
    """
    has_title = any(z["role"] == "title" for z in zones)
    has_subtitle = any(z["role"] == "subtitle" for z in zones)
    has_chart = any(z["role"] == "chart" for z in zones)
    has_table = any(z["role"] == "table" for z in zones)
    has_footer = any(z["role"] == "footer" for z in zones)
    content_zones = [z for z in zones if z["role"] == "content"]
    n_content = len(content_zones)
    all_zones = [z for z in zones if z["role"] not in ("footer", "decorative")]
    n_meaningful = len(all_zones)

    # Media: only count substantial media zones (not tiny icons)
    media_zones = [z for z in zones if z["role"] == "media"]
    substantial_media = [
        z for z in media_zones
        if z["bounds_pct"]["width"] * z["bounds_pct"]["height"] > 0.05
    ]
    has_media = len(substantial_media) > 0
    n_media = len(substantial_media)

    # --- Opening: first slide ---
    if slide_idx == 0:
        return "opening"

    # --- Closing: last slide ---
    if slide_idx == total_slides - 1:
        return "closing"

    # --- Visualize: has chart ---
    if has_chart:
        return "visualize"

    # --- Tabulate: has table ---
    if has_table:
        return "tabulate"

    # --- Illustrate: has image/media alongside content ---
    if has_media and n_content >= 1:
        return "illustrate"
    if has_media and has_title:
        return "illustrate"

    # --- Section break: minimal content, large title, special background ---
    if has_title and n_content == 0 and not has_chart and not has_table:
        title_zone = next((z for z in zones if z["role"] == "title"), None)
        font_size = title_zone.get("font_size_pt") if title_zone else None
        if font_size and font_size >= 24:
            return "section_break"
        if bg_type == "gradient":
            return "section_break"
        if has_subtitle and n_meaningful <= 3:
            return "section_break"

    # --- Emphasize: title + one small content zone with large text ---
    if has_title and n_content == 1:
        cz = content_zones[0]
        text = cz.get("text_sample", "")
        font_size = cz.get("font_size_pt")
        # Large font or very short text = emphasis slide (big number, quote)
        if font_size and font_size >= 24:
            return "emphasize"
        if len(text) < 50 and cz["bounds_pct"]["height"] > 0.2:
            return "emphasize"

    # --- Compare: multiple content zones arranged as columns ---
    if n_cols >= 2 and n_content >= 2:
        return "compare"

    # --- Multi-content without columns: could be stacked sections ---
    if n_content >= 3 and n_cols == 1:
        # Multiple stacked content areas = explain (not compare)
        return "explain"

    if n_content == 2 and n_cols == 1:
        # Two stacked content zones = explain with sub-sections
        # Check if they're vertically stacked (different tops, similar lefts)
        tops = [z["bounds_pct"]["top"] for z in content_zones]
        lefts = [z["bounds_pct"]["left"] for z in content_zones]
        if abs(lefts[0] - lefts[1]) < 0.1:
            return "explain"  # vertically stacked
        else:
            return "compare"  # side by side but column detection missed it

    # --- Explain: title + single content zone ---
    if has_title and n_content == 1:
        return "explain"

    # --- Outline: multiple small text items (numbered list, agenda) ---
    if has_title and n_content == 0 and n_meaningful <= 2:
        # Just a title, maybe subtitle -- could be section break or transition
        return "section_break"

    # --- Media-only slide ---
    if has_media and n_content == 0:
        return "illustrate"

    # --- Fallback based on content count ---
    if n_content >= 1:
        return "explain"

    return "general"


def _detect_columns(zones):
    """Detect number of content columns from zone positions.

    Uses overlap analysis on meaningful zones only (content, media with
    reasonable size). Caps at 4 columns -- higher counts indicate icon
    grids or other non-layout patterns.
    """
    MAX_REALISTIC_COLS = 4

    # Only consider substantial zones for column detection
    meaningful_zones = [
        z for z in zones
        if z["role"] in ("content", "media")
        and z["bounds_pct"]["width"] * z["bounds_pct"]["height"] > 0.03
    ]
    if len(meaningful_zones) < 2:
        return 1

    # Sort by left position
    sorted_zones = sorted(meaningful_zones, key=lambda z: z["bounds_pct"]["left"])

    # Check if zones form columns (non-overlapping horizontally, overlapping vertically)
    columns = [sorted_zones[0]]
    for zone in sorted_zones[1:]:
        prev = columns[-1]
        prev_right = prev["bounds_pct"]["left"] + prev["bounds_pct"]["width"]
        curr_left = zone["bounds_pct"]["left"]

        # Horizontal gap (no significant overlap)
        h_gap = curr_left - prev_right
        if h_gap > -0.05:  # allow tiny overlap (5%) from rounding
            # Vertical overlap check: do they share vertical space?
            prev_top = prev["bounds_pct"]["top"]
            prev_bot = prev_top + prev["bounds_pct"]["height"]
            curr_top = zone["bounds_pct"]["top"]
            curr_bot = curr_top + zone["bounds_pct"]["height"]

            overlap_top = max(prev_top, curr_top)
            overlap_bot = min(prev_bot, curr_bot)
            v_overlap = max(0, overlap_bot - overlap_top)

            min_height = min(prev["bounds_pct"]["height"], zone["bounds_pct"]["height"])
            if min_height > 0 and v_overlap / min_height > 0.3:
                columns.append(zone)

    n_cols = len(columns)
    if n_cols >= 2:
        return min(n_cols, MAX_REALISTIC_COLS)

    # Fallback: check if tops are similar and lefts are spread
    tops = [z["bounds_pct"]["top"] for z in meaningful_zones]
    lefts = [z["bounds_pct"]["left"] for z in meaningful_zones]
    top_spread = max(tops) - min(tops)
    left_spread = max(lefts) - min(lefts)

    if top_spread < 0.10 and left_spread > 0.15:
        return min(len(meaningful_zones), MAX_REALISTIC_COLS)

    return 1


# ---------------------------------------------------------------------------
# Spacing extraction
# ---------------------------------------------------------------------------

def extract_spacing(prs, layouts):
    """Extract spacing patterns from extracted layouts."""
    margin_lefts = []
    margin_tops = []
    margin_rights = []
    margin_bottoms = []
    gutters = []

    slide_width = prs.slide_width
    slide_height = prs.slide_height

    for layout in layouts:
        for zone in layout["zones"]:
            b = zone["bounds_pct"]
            margin_lefts.append(b["left"])
            margin_tops.append(b["top"])
            margin_rights.append(1.0 - b["left"] - b["width"])
            margin_bottoms.append(1.0 - b["top"] - b["height"])

        # Detect gutter between side-by-side content zones
        content_zones = sorted(
            [z for z in layout["zones"] if z["role"] == "content"],
            key=lambda z: z["bounds_pct"]["left"]
        )
        for i in range(len(content_zones) - 1):
            z1 = content_zones[i]["bounds_pct"]
            z2 = content_zones[i + 1]["bounds_pct"]
            gap = z2["left"] - (z1["left"] + z1["width"])
            if 0.01 < gap < 0.15:
                gutters.append(gap)

    def _median(values):
        if not values:
            return 0.0
        s = sorted(values)
        n = len(s)
        return round(s[n // 2], 4)

    return {
        "margin_left_pct": _median(margin_lefts),
        "margin_top_pct": _median(margin_tops),
        "margin_right_pct": _median(margin_rights),
        "margin_bottom_pct": _median(margin_bottoms),
        "typical_gutter_pct": _median(gutters) if gutters else 0.03,
    }


# ---------------------------------------------------------------------------
# Decorative element extraction
# ---------------------------------------------------------------------------

def extract_decorative_patterns(layouts):
    """Summarize recurring decorative elements across slides."""
    pattern_counts = Counter()
    pattern_examples = defaultdict(list)

    for layout in layouts:
        for dec in layout["decorative_shapes"]:
            dtype = dec["inferred_type"]
            pattern_counts[dtype] += 1
            if len(pattern_examples[dtype]) < 3:
                pattern_examples[dtype].append({
                    "bounds_pct": dec["bounds_pct"],
                    "fill": dec.get("fill"),
                })

    return [
        {
            "type": dtype,
            "count": count,
            "examples": pattern_examples[dtype],
        }
        for dtype, count in pattern_counts.most_common(10)
    ]


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def extract_profile(pptx_path, source_id=None):
    """Extract a complete style profile from a PPTX file."""
    prs = Presentation(pptx_path)

    slide_width = prs.slide_width
    slide_height = prs.slide_height

    # Resolve theme fonts first -- used by typography extraction
    theme_fonts = _resolve_theme_fonts(prs)

    layouts = extract_layouts(prs)

    profile = {
        "source_id": source_id or os.path.splitext(os.path.basename(pptx_path))[0],
        "source_file": os.path.basename(pptx_path),
        "slide_count": len(prs.slides),
        "slide_dimensions": {
            "width_emu": slide_width,
            "height_emu": slide_height,
            "width_inches": round(slide_width / 914400, 3),
            "height_inches": round(slide_height / 914400, 3),
        },
        "theme_fonts": theme_fonts,
        "colors": extract_colors(prs),
        "typography": extract_typography(prs, theme_fonts),
        "layouts": layouts,
        "spacing": extract_spacing(prs, layouts),
        "decorative_patterns": extract_decorative_patterns(layouts),
    }

    return profile


def main():
    parser = argparse.ArgumentParser(description="Extract style profiles from PPTX files")
    parser.add_argument("pptx_path", nargs="?", help="Path to a single PPTX file")
    parser.add_argument("--all", action="store_true", help="Extract all files in raw/")
    parser.add_argument("--output-dir", default=PROFILES_DIR, help="Output directory for profiles")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.all:
        pptx_files = sorted([
            f for f in os.listdir(RAW_DIR)
            if f.endswith(".pptx")
        ])
        if not pptx_files:
            print(f"No PPTX files found in {RAW_DIR}")
            sys.exit(1)

        print(f"Extracting {len(pptx_files)} files...")
        for i, filename in enumerate(pptx_files):
            src_id = os.path.splitext(filename)[0]
            pptx_path = os.path.join(RAW_DIR, filename)
            out_path = os.path.join(args.output_dir, f"{src_id}.json")

            print(f"[{i+1}/{len(pptx_files)}] {src_id}...", end=" ")
            try:
                profile = extract_profile(pptx_path, source_id=src_id)
                with open(out_path, "w") as f:
                    json.dump(profile, f, indent=2)
                print(f"OK ({profile['slide_count']} slides)")
            except Exception as e:
                print(f"FAILED: {e}")

    elif args.pptx_path:
        src_id = os.path.splitext(os.path.basename(args.pptx_path))[0]
        profile = extract_profile(args.pptx_path, source_id=src_id)
        out_path = os.path.join(args.output_dir, f"{src_id}.json")
        with open(out_path, "w") as f:
            json.dump(profile, f, indent=2)
        print(f"Profile saved to {out_path} ({profile['slide_count']} slides)")
        print(f"  Colors: {len(profile['colors']['sampled_fills'])} fill colors, "
              f"{len(profile['colors']['theme_colors'])} theme colors")
        print(f"  Typography: {len(profile['typography']['fonts_used'])} fonts, "
              f"{len(profile['typography']['hierarchy'])} hierarchy levels")
        print(f"  Layouts: {len(profile['layouts'])} slides analyzed")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
