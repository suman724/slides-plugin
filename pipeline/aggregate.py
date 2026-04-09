#!/usr/bin/env python3
"""Aggregate per-file style profiles into a unified style library.

Reads all JSON profiles from pipeline/profiles/, clusters colors,
typography, and layouts, and outputs style_library.json.

Usage:
    python3 aggregate.py
    python3 aggregate.py --output path/to/style_library.json
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(SCRIPT_DIR, "profiles")
DEFAULT_OUTPUT = os.path.join(
    SCRIPT_DIR, "..", "skills", "slides", "scripts", "style_library.json"
)


# ---------------------------------------------------------------------------
# Color utilities
# ---------------------------------------------------------------------------

def hex_to_rgb(h):
    """Convert hex string to (R, G, B) tuple."""
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_lab(rgb):
    """Convert RGB to CIE LAB (approximate, for distance calculation)."""
    # Normalize to 0-1
    r, g, b = [c / 255.0 for c in rgb]

    # sRGB to linear
    def linearize(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = linearize(r), linearize(g), linearize(b)

    # Linear RGB to XYZ (D65)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    # XYZ to LAB
    def f(t):
        return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116

    xn, yn, zn = 0.95047, 1.0, 1.08883
    l = 116 * f(y / yn) - 16
    a = 500 * (f(x / xn) - f(y / yn))
    b_val = 200 * (f(y / yn) - f(z / zn))

    return (l, a, b_val)


def color_distance(hex1, hex2):
    """Delta E (CIE76) distance between two hex colors."""
    lab1 = rgb_to_lab(hex_to_rgb(hex1))
    lab2 = rgb_to_lab(hex_to_rgb(hex2))
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def _infer_mood(colors):
    """Infer palette mood from color properties."""
    primary = hex_to_rgb(colors.get("primary", "#000000"))
    bg = hex_to_rgb(colors.get("background", "#FFFFFF"))

    # Dark background = bold/dark mood
    bg_brightness = sum(bg) / 3
    if bg_brightness < 60:
        return "bold"

    # Warm primary (red/orange/yellow hue)
    r, g, b = primary
    if r > 150 and r > g and r > b:
        return "warm"
    if r > 100 and g > 80 and b < 80:
        return "warm"

    # Cool primary (blue/green)
    if b > r and b > 100:
        return "professional"
    if g > r and g > 100:
        return "fresh"

    # Light, low-saturation = minimal
    primary_brightness = sum(primary) / 3
    if primary_brightness > 200:
        return "minimal"

    return "professional"


def _infer_temperature(colors):
    """Infer warm/cool/neutral from primary color."""
    primary = hex_to_rgb(colors.get("primary", "#808080"))
    r, g, b = primary
    if r > b + 30:
        return "warm"
    if b > r + 30:
        return "cool"
    return "neutral"


# ---------------------------------------------------------------------------
# Palette aggregation
# ---------------------------------------------------------------------------

def aggregate_palettes(profiles):
    """Build color palettes from profile theme colors and sampled fills."""
    raw_palettes = []

    for profile in profiles:
        colors = profile["colors"]
        theme = colors.get("theme_colors", {})
        fills = colors.get("sampled_fills", [])
        text_colors = colors.get("sampled_text_colors", [])

        # Build a palette from theme colors if available
        palette_colors = {}
        if theme:
            palette_colors["primary"] = theme.get("dk2", theme.get("accent1", "#333333"))
            palette_colors["secondary"] = theme.get("accent1", theme.get("dk2", "#666666"))
            palette_colors["accent"] = theme.get("accent2", theme.get("accent3", "#FF8800"))
            palette_colors["accent_alt"] = theme.get("accent3", theme.get("accent4", "#008844"))
            palette_colors["text_primary"] = theme.get("dk1", "#1A1A1A")
            palette_colors["text_secondary"] = "#4A4A4A"  # common default
            palette_colors["text_on_dark"] = theme.get("lt1", "#FFFFFF")
            palette_colors["background"] = theme.get("lt1", "#FFFFFF")
            palette_colors["background_alt"] = theme.get("lt2", "#F0F0F0")
        elif fills:
            # Fallback: use sampled fills
            palette_colors["primary"] = fills[0] if len(fills) > 0 else "#333333"
            palette_colors["secondary"] = fills[1] if len(fills) > 1 else "#666666"
            palette_colors["accent"] = fills[2] if len(fills) > 2 else "#FF8800"
            palette_colors["accent_alt"] = fills[3] if len(fills) > 3 else "#008844"
            palette_colors["text_primary"] = text_colors[0] if text_colors else "#1A1A1A"
            palette_colors["text_secondary"] = "#4A4A4A"
            palette_colors["text_on_dark"] = "#FFFFFF"
            palette_colors["background"] = "#FFFFFF"
            palette_colors["background_alt"] = "#F5F5F5"
        else:
            continue

        # Add positive/negative defaults
        palette_colors["positive"] = "#2D8F5E"
        palette_colors["negative"] = "#C0392B"

        # Build chart palette from accents
        chart_colors = []
        for key in ["primary", "accent", "accent_alt", "secondary"]:
            if key in palette_colors:
                chart_colors.append(palette_colors[key])
        chart_colors.extend(["#C0392B", "#6C5B7B"])  # fill out to 6

        # Gradient pairs
        gradient_pairs = []
        gradient_stops = colors.get("gradient_stops", [])
        if gradient_stops:
            gradient_pairs = [gradient_stops[0][:2]] if len(gradient_stops[0]) >= 2 else []
        if not gradient_pairs and "primary" in palette_colors and "secondary" in palette_colors:
            gradient_pairs = [[palette_colors["primary"], palette_colors["secondary"]]]

        raw_palettes.append({
            "source_id": profile["source_id"],
            "colors": palette_colors,
            "chart_colors": chart_colors[:6],
            "gradient_pairs": gradient_pairs,
        })

    # Cluster similar palettes by primary color distance
    clusters = _cluster_palettes(raw_palettes)

    # Build final palettes
    palettes = []
    for i, cluster in enumerate(clusters):
        # Use the first palette in the cluster as representative
        rep = cluster[0]
        source_ids = [p["source_id"] for p in cluster]
        mood = _infer_mood(rep["colors"])
        temp = _infer_temperature(rep["colors"])

        palette_id = f"palette-{i+1:02d}-{mood}"

        palettes.append({
            "id": palette_id,
            "mood": mood,
            "temperature": temp,
            "source_ids": source_ids,
            "colors": rep["colors"],
            "chart_colors": rep["chart_colors"],
            "gradient_pairs": rep["gradient_pairs"],
        })

    return palettes


def _cluster_palettes(raw_palettes, distance_threshold=35):
    """Simple greedy clustering of palettes by primary color similarity."""
    clusters = []

    for palette in raw_palettes:
        primary = palette["colors"].get("primary", "#000000")
        assigned = False

        for cluster in clusters:
            rep_primary = cluster[0]["colors"].get("primary", "#000000")
            dist = color_distance(primary, rep_primary)
            if dist < distance_threshold:
                cluster.append(palette)
                assigned = True
                break

        if not assigned:
            clusters.append([palette])

    return clusters


# ---------------------------------------------------------------------------
# Typography aggregation
# ---------------------------------------------------------------------------

def aggregate_typography(profiles):
    """Cluster typography patterns across profiles."""
    patterns = []

    for profile in profiles:
        typo = profile["typography"]
        hierarchy = typo.get("hierarchy", {})
        fonts = typo.get("fonts_used", [])

        if not hierarchy or not fonts:
            continue

        primary_font = fonts[0]["name"] if fonts else "Calibri"
        fallback = fonts[1]["name"] if len(fonts) > 1 else "Arial"

        patterns.append({
            "source_id": profile["source_id"],
            "font_family": primary_font,
            "fallback": fallback,
            "hierarchy": hierarchy,
        })

    # Cluster by font family
    font_groups = defaultdict(list)
    for p in patterns:
        font_groups[p["font_family"]].append(p)

    result = []
    for i, (font, members) in enumerate(sorted(font_groups.items(), key=lambda x: -len(x[1]))):
        # Use median sizes from the group
        merged_hierarchy = _merge_hierarchies([m["hierarchy"] for m in members])
        fallback = members[0]["fallback"]
        source_ids = [m["source_id"] for m in members]

        typo_id = f"typo-{font.lower().replace(' ', '-')}"

        result.append({
            "id": typo_id,
            "font_family": font,
            "fallback": fallback,
            "source_ids": source_ids,
            "hierarchy": merged_hierarchy,
        })

    return result


def _merge_hierarchies(hierarchies):
    """Merge multiple typography hierarchies by taking median sizes."""
    roles = ["display", "title", "heading", "body", "body_small", "caption", "metric", "footer"]
    merged = {}

    for role in roles:
        sizes = []
        fonts = []
        bolds = []
        for h in hierarchies:
            if role in h:
                sizes.append(h[role]["size_pt"])
                fonts.append(h[role].get("font", "Calibri"))
                bolds.append(h[role].get("bold", False))

        if sizes:
            median_size = float(np.median(sizes))
            most_common_font = Counter(fonts).most_common(1)[0][0]
            most_common_bold = Counter(bolds).most_common(1)[0][0]
            merged[role] = {
                "size_pt": round(median_size, 1),
                "bold": most_common_bold,
            }

    return merged


# ---------------------------------------------------------------------------
# Layout pattern aggregation
# ---------------------------------------------------------------------------

def aggregate_layouts(profiles):
    """Discover layout patterns by clustering slides across all profiles."""
    all_slides = []

    for profile in profiles:
        for layout in profile.get("layouts", []):
            zones = layout["zones"]

            # --- Filter out noise slides ---
            # Skip slides with no meaningful zones
            meaningful = [z for z in zones if z["role"] not in ("footer", "decorative")]
            if not meaningful:
                continue

            # Skip slides with too many media zones (icon grids, image galleries)
            media_count = sum(1 for z in zones if z["role"] == "media")
            if media_count > 6:
                continue

            # Skip slides with too many total zones (noise/complex infographics)
            if len(zones) > 15:
                continue

            all_slides.append({
                "source_id": profile["source_id"],
                "slide_index": layout["slide_index"],
                "purpose": layout["inferred_purpose"],
                "n_columns": layout.get("n_columns", 1),
                "background": layout.get("background", {"type": "solid", "colors": []}),
                "zones": zones,
                "decorative_shapes": layout.get("decorative_shapes", []),
            })

    # Compute structural signature for each slide
    signatures = []
    for slide in all_slides:
        sig = _compute_signature(slide)
        signatures.append(sig)

    # Cluster by signature similarity
    clusters = _cluster_by_signature(all_slides, signatures)

    # Build discovered patterns
    discovered = []
    for i, cluster in enumerate(clusters):
        if len(cluster) < 2:  # need at least 2 slides to form a pattern
            continue

        # Compute median zones
        purpose = Counter(s["purpose"] for s in cluster).most_common(1)[0][0]
        n_cols = Counter(s["n_columns"] for s in cluster).most_common(1)[0][0]
        bg_type = Counter(s["background"]["type"] for s in cluster).most_common(1)[0][0]
        source_ids = list(set(s["source_id"] for s in cluster))

        # Skip "general" purpose -- these are unclassifiable noise
        if purpose == "general":
            continue

        median_zones = _compute_median_zones(cluster)

        # Skip patterns with no meaningful zones after median computation
        meaningful_zones = [z for z in median_zones if z["role"] not in ("footer", "decorative")]
        if not meaningful_zones:
            continue

        # Collect decorative patterns
        dec_types = Counter()
        for s in cluster:
            for d in s.get("decorative_shapes", []):
                dec_types[d.get("inferred_type", "shape")] += 1
        decorative = [dt for dt, count in dec_types.most_common(3) if count >= len(cluster) * 0.3]

        # Confidence: based on cluster size and source diversity
        n_unique_sources = len(source_ids)
        confidence = min(1.0, len(cluster) / 10.0) * min(1.0, n_unique_sources / 3.0)

        pattern_id = f"discovered-{purpose}-{n_cols}col-v{i+1}"

        discovered.append({
            "id": pattern_id,
            "purpose": purpose,
            "source_count": len(cluster),
            "confidence": round(confidence, 2),
            "source_ids": source_ids[:10],
            "background_type": bg_type,
            "n_columns": n_cols,
            "zones": median_zones,
            "decorative": decorative,
        })

    # Sort by source_count descending
    discovered.sort(key=lambda x: -x["source_count"])

    return discovered


def _compute_signature(slide):
    """Compute a hashable structural signature for a slide."""
    roles = tuple(sorted(z["role"] for z in slide["zones"]))
    n_zones = len(slide["zones"])
    n_cols = slide.get("n_columns", 1)
    purpose = slide["purpose"]
    bg = slide["background"]["type"]
    return (roles, n_zones, n_cols, purpose, bg)


def _cluster_by_signature(slides, signatures):
    """Group slides with identical or very similar signatures."""
    clusters = defaultdict(list)
    for slide, sig in zip(slides, signatures):
        clusters[sig].append(slide)

    return list(clusters.values())


def _compute_median_zones(cluster):
    """Compute median zone positions across cluster members."""
    # Group zones by role
    role_positions = defaultdict(list)
    for slide in cluster:
        for zone in slide["zones"]:
            role = zone["role"]
            role_positions[role].append(zone["bounds_pct"])

    median_zones = []
    for role, positions in role_positions.items():
        if len(positions) < 2:
            # Use the single position as-is
            median_zones.append({"role": role, "bounds_pct": positions[0]})
            continue

        lefts = [p["left"] for p in positions]
        tops = [p["top"] for p in positions]
        widths = [p["width"] for p in positions]
        heights = [p["height"] for p in positions]

        median_zones.append({
            "role": role,
            "bounds_pct": {
                "left": round(float(np.median(lefts)), 4),
                "top": round(float(np.median(tops)), 4),
                "width": round(float(np.median(widths)), 4),
                "height": round(float(np.median(heights)), 4),
            },
        })

    return median_zones


# ---------------------------------------------------------------------------
# Decorative element aggregation
# ---------------------------------------------------------------------------

def aggregate_decorative(profiles):
    """Aggregate decorative patterns across all profiles."""
    all_patterns = Counter()
    all_examples = defaultdict(list)

    for profile in profiles:
        for pattern in profile.get("decorative_patterns", []):
            dtype = pattern["type"]
            all_patterns[dtype] += pattern["count"]
            for ex in pattern.get("examples", []):
                if len(all_examples[dtype]) < 5:
                    all_examples[dtype].append(ex)

    result = {}
    for dtype, count in all_patterns.most_common(10):
        examples = all_examples[dtype]
        # Compute median position from examples
        if examples:
            median_bounds = {
                "left": round(float(np.median([e["bounds_pct"]["left"] for e in examples])), 4),
                "top": round(float(np.median([e["bounds_pct"]["top"] for e in examples])), 4),
                "width": round(float(np.median([e["bounds_pct"]["width"] for e in examples])), 4),
                "height": round(float(np.median([e["bounds_pct"]["height"] for e in examples])), 4),
            }
        else:
            median_bounds = {}

        result[dtype] = {
            "total_count": count,
            "median_bounds_pct": median_bounds,
        }

    return result


# ---------------------------------------------------------------------------
# Spacing aggregation
# ---------------------------------------------------------------------------

def aggregate_spacing(profiles):
    """Compute median spacing across all profiles."""
    keys = ["margin_left_pct", "margin_top_pct", "margin_right_pct",
            "margin_bottom_pct", "typical_gutter_pct"]

    values = defaultdict(list)
    for profile in profiles:
        spacing = profile.get("spacing", {})
        for key in keys:
            if key in spacing and spacing[key] > 0:
                values[key].append(spacing[key])

    return {
        key: round(float(np.median(vals)), 4) if vals else 0.05
        for key, vals in values.items()
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def aggregate(profiles):
    """Build the complete style library from profiles."""
    return {
        "version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(profiles),
        "palettes": aggregate_palettes(profiles),
        "typography_patterns": aggregate_typography(profiles),
        "discovered_patterns": aggregate_layouts(profiles),
        "decorative_elements": aggregate_decorative(profiles),
        "spacing_defaults": aggregate_spacing(profiles),
    }


def main():
    parser = argparse.ArgumentParser(description="Aggregate profiles into style library")
    parser.add_argument("--profiles-dir", default=PROFILES_DIR, help="Profiles directory")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output style_library.json path")
    args = parser.parse_args()

    # Load all profiles
    profile_files = sorted([
        f for f in os.listdir(args.profiles_dir)
        if f.endswith(".json")
    ])

    if not profile_files:
        print(f"No profile JSON files found in {args.profiles_dir}")
        sys.exit(1)

    print(f"Loading {len(profile_files)} profiles...")
    profiles = []
    for filename in profile_files:
        with open(os.path.join(args.profiles_dir, filename)) as f:
            profiles.append(json.load(f))

    print("Aggregating...")
    library = aggregate(profiles)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with open(args.output, "w") as f:
        json.dump(library, f, indent=2)

    print(f"\nStyle library saved to: {args.output}")
    print(f"  Palettes: {len(library['palettes'])}")
    print(f"  Typography patterns: {len(library['typography_patterns'])}")
    print(f"  Discovered layout patterns: {len(library['discovered_patterns'])}")
    print(f"  Decorative elements: {len(library['decorative_elements'])}")


if __name__ == "__main__":
    main()
