"""Map semantic intents to layout patterns from the style library.

Uses the hybrid approach:
1. Search discovered patterns by matching purpose tag
2. Fall back to structural fallback patterns
3. Last resort: fallback-content

Also handles content-adaptive overrides (e.g., 3 compare sides -> categorize).
"""

from style_resolver import load_library


# ---------------------------------------------------------------------------
# Intent-to-purpose mapping
# ---------------------------------------------------------------------------

INTENT_TO_PURPOSE = {
    "open":        "opening",
    "close":       "closing",
    "outline":     "explain",       # no dedicated outline purpose in extraction
    "divide":      "section_break",
    "explain":     "explain",
    "compare":     "compare",
    "categorize":  "compare",       # 3-col compare
    "measure":     "explain",       # metrics rendered into content zone
    "visualize":   "visualize",
    "tabulate":    "tabulate",
    "evaluate":    "compare",
    "sequence":    "explain",       # timeline rendered into content zone
    "emphasize":   "emphasize",
    "illustrate":  "illustrate",
    "summarize":   "explain",       # numbered list rendered into content zone
}


# ---------------------------------------------------------------------------
# Structural fallbacks
# ---------------------------------------------------------------------------

STRUCTURAL_FALLBACKS = {
    "fallback-cover": {
        "id": "fallback-cover",
        "purpose": "opening",
        "background_type": "gradient",
        "n_columns": 1,
        "zones": [
            {"role": "title",    "bounds_pct": {"left": 0.10, "top": 0.27, "width": 0.80, "height": 0.16}},
            {"role": "subtitle", "bounds_pct": {"left": 0.10, "top": 0.44, "width": 0.80, "height": 0.08}},
        ],
        "decorative": [],
    },
    "fallback-close": {
        "id": "fallback-close",
        "purpose": "closing",
        "background_type": "gradient",
        "n_columns": 1,
        "zones": [
            {"role": "title",    "bounds_pct": {"left": 0.10, "top": 0.29, "width": 0.80, "height": 0.13}},
            {"role": "subtitle", "bounds_pct": {"left": 0.10, "top": 0.45, "width": 0.80, "height": 0.08}},
            {"role": "contact",  "bounds_pct": {"left": 0.10, "top": 0.57, "width": 0.80, "height": 0.05}},
        ],
        "decorative": [],
    },
    "fallback-divider": {
        "id": "fallback-divider",
        "purpose": "section_break",
        "background_type": "solid",
        "n_columns": 1,
        "zones": [
            {"role": "panel",    "bounds_pct": {"left": 0.0,   "top": 0.0,   "width": 0.338, "height": 1.0}},
            {"role": "number",   "bounds_pct": {"left": 0.038, "top": 0.27,  "width": 0.263, "height": 0.20}},
            {"role": "title",    "bounds_pct": {"left": 0.39,  "top": 0.29,  "width": 0.555, "height": 0.13}},
            {"role": "subtitle", "bounds_pct": {"left": 0.39,  "top": 0.47,  "width": 0.555, "height": 0.08}},
        ],
        "decorative": ["accent_bar"],
    },
    "fallback-content": {
        "id": "fallback-content",
        "purpose": "general",
        "background_type": "solid",
        "n_columns": 1,
        "zones": [
            {"role": "title",   "bounds_pct": {"left": 0.056, "top": 0.053, "width": 0.888, "height": 0.107}},
            {"role": "content", "bounds_pct": {"left": 0.071, "top": 0.200, "width": 0.858, "height": 0.650}},
        ],
        "decorative": ["accent_bar"],
    },
}

# Intent -> fallback ID
INTENT_TO_FALLBACK = {
    "open":    "fallback-cover",
    "close":   "fallback-close",
    "divide":  "fallback-divider",
}


# ---------------------------------------------------------------------------
# Content-adaptive overrides
# ---------------------------------------------------------------------------

def _adapt_intent(intent, slide_spec):
    """Adjust intent based on content analysis."""
    if intent == "compare":
        sides = slide_spec.get("sides", [])
        if len(sides) >= 3:
            return "categorize"

    if intent == "evaluate":
        options = slide_spec.get("options", [])
        if len(options) >= 3:
            return "categorize"

    if intent == "explain":
        points = slide_spec.get("points", [])
        # Single short point -> emphasize instead
        if len(points) == 1:
            p = points[0]
            text = p.get("text", "") if isinstance(p, dict) else str(p)
            if len(text) < 50:
                return "emphasize"

    return intent


# ---------------------------------------------------------------------------
# Content-to-zone mapping
# ---------------------------------------------------------------------------

def map_content_to_zones(intent, slide_spec, layout_pattern):
    """Map semantic content fields to zone roles.

    Returns a dict of {zone_role: content_data} that the layout engine
    uses to render content into each zone.
    """
    zones = {z["role"]: z for z in layout_pattern["zones"]}
    mapping = {}

    # Title is universal
    if "title" in zones:
        mapping["title"] = slide_spec.get("title", "")

    # Subtitle
    if "subtitle" in zones:
        mapping["subtitle"] = slide_spec.get("subtitle", "")

    # Contact (closing slides)
    if "contact" in zones:
        mapping["contact"] = slide_spec.get("contact", "")

    # Panel + number (section dividers)
    if "panel" in zones:
        mapping["panel"] = True
    if "number" in zones:
        mapping["number"] = slide_spec.get("section_number", "")

    # Content zone -- maps differently per intent
    # Skip content zone if a dedicated zone already handles the data
    # (e.g., don't put chart in content zone if a chart zone exists)
    has_dedicated_chart = "chart" in zones
    has_dedicated_table = "table" in zones

    if "content" in zones:
        if intent == "explain":
            mapping["content"] = {"type": "bullets", "data": slide_spec.get("points", [])}
        elif intent == "outline":
            mapping["content"] = {"type": "numbered_items", "data": slide_spec.get("items", [])}
        elif intent == "compare":
            sides = slide_spec.get("sides", [])
            mapping["content"] = {"type": "columns", "data": sides}
        elif intent == "categorize":
            sides = slide_spec.get("sides", slide_spec.get("columns", []))
            mapping["content"] = {"type": "columns", "data": sides}
        elif intent == "measure":
            mapping["content"] = {"type": "metrics", "data": slide_spec.get("metrics", [])}
        elif intent == "visualize" and not has_dedicated_chart:
            mapping["content"] = {"type": "chart", "data": slide_spec.get("chart", {})}
        elif intent == "tabulate" and not has_dedicated_table:
            mapping["content"] = {
                "type": "table",
                "columns": slide_spec.get("columns", []),
                "rows": slide_spec.get("rows", []),
                "highlight_rules": slide_spec.get("highlight_rules", []),
            }
        elif intent == "evaluate":
            mapping["content"] = {"type": "evaluation", "data": slide_spec.get("options", [])}
        elif intent == "sequence":
            mapping["content"] = {"type": "timeline", "data": slide_spec.get("steps", [])}
        elif intent == "emphasize":
            mapping["content"] = {"type": "emphasis", "data": slide_spec.get("emphasis", {})}
        elif intent == "summarize":
            mapping["content"] = {
                "type": "takeaway",
                "takeaways": slide_spec.get("takeaways", []),
                "action": slide_spec.get("action", ""),
            }
        else:
            mapping["content"] = {"type": "text", "data": slide_spec.get("text", "")}

    # Table zone (dedicated table layouts)
    if "table" in zones:
        mapping["table"] = {
            "columns": slide_spec.get("columns", []),
            "rows": slide_spec.get("rows", []),
            "highlight_rules": slide_spec.get("highlight_rules", []),
        }

    # Chart zone (dedicated chart layouts)
    if "chart" in zones:
        mapping["chart"] = slide_spec.get("chart", {})

    # Media zone
    if "media" in zones:
        mapping["media"] = slide_spec.get("image_path", "")

    # Annotation / note
    if "annotation" in zones:
        mapping["annotation"] = slide_spec.get("note", slide_spec.get("annotation", ""))

    # Footer data (from metadata, handled by layout engine)
    if "footer" in zones:
        mapping["footer"] = True

    return mapping


# ---------------------------------------------------------------------------
# Main resolution
# ---------------------------------------------------------------------------

def resolve_layout(intent, slide_spec):
    """Resolve a semantic intent to a layout pattern + content mapping.

    Returns:
        (layout_pattern, content_mapping, adapted_intent)
    """
    library = load_library()
    discovered = library.get("discovered_patterns", [])

    # Apply content-adaptive overrides
    adapted_intent = _adapt_intent(intent, slide_spec)

    # Structural intents always use fallbacks -- they have specific zone needs
    # that discovered patterns rarely satisfy
    if adapted_intent in INTENT_TO_FALLBACK:
        fallback_id = INTENT_TO_FALLBACK[adapted_intent]
        pattern = STRUCTURAL_FALLBACKS[fallback_id]
        content_mapping = map_content_to_zones(adapted_intent, slide_spec, pattern)
        return pattern, content_mapping, adapted_intent

    purpose = INTENT_TO_PURPOSE.get(adapted_intent, "explain")

    # Preferred column count based on content
    preferred_cols = _preferred_columns(adapted_intent, slide_spec)

    # 1. Search discovered patterns by purpose
    candidates = [p for p in discovered if p["purpose"] == purpose]

    # Prefer patterns matching preferred column count
    if preferred_cols > 1:
        col_matches = [p for p in candidates if p["n_columns"] == preferred_cols]
        if col_matches:
            candidates = col_matches

    # Sort by confidence * source_count (best first)
    candidates.sort(key=lambda p: -(p.get("confidence", 0) * p.get("source_count", 0)))

    # Validate candidates have the zones we need for this intent
    required_roles = _required_zones(adapted_intent)
    if required_roles:
        candidates = [
            p for p in candidates
            if required_roles.issubset({z["role"] for z in p["zones"]})
        ] or candidates  # fall back to unfiltered if nothing matches

    if candidates:
        pattern = candidates[0]
    else:
        # 2. Fall back to structural fallback
        fallback_id = INTENT_TO_FALLBACK.get(adapted_intent, "fallback-content")
        pattern = STRUCTURAL_FALLBACKS[fallback_id]

    # 3. Ensure content zones are wide enough for the intent
    pattern = _enforce_min_zone_width(pattern, adapted_intent)

    # 4. Map content to zones
    content_mapping = map_content_to_zones(adapted_intent, slide_spec, pattern)

    return pattern, content_mapping, adapted_intent


def _enforce_min_zone_width(pattern, intent):
    """Ensure content zones meet minimum width for the intent.

    Some discovered patterns have narrow content zones that don't work
    for compare/evaluate/tabulate. Widen them if needed.
    """
    # Intents that need wide content zones
    WIDE_INTENTS = {"compare", "categorize", "evaluate", "tabulate", "measure", "sequence"}
    if intent not in WIDE_INTENTS:
        return pattern

    MIN_CONTENT_LEFT = 0.056   # ~0.75" at 13.333" slide
    MIN_CONTENT_WIDTH = 0.85   # at least 85% of slide width

    zones = pattern.get("zones", [])
    adjusted = False

    new_zones = []
    for zone in zones:
        b = zone["bounds_pct"]
        if zone["role"] == "content" and b["width"] < MIN_CONTENT_WIDTH:
            # Deep copy to avoid mutating the cached library pattern
            new_zone = {"role": zone["role"], "bounds_pct": {
                "left": MIN_CONTENT_LEFT,
                "top": b["top"],
                "width": MIN_CONTENT_WIDTH,
                "height": b["height"],
            }}
            new_zones.append(new_zone)
            adjusted = True
        else:
            new_zones.append(zone)

    if adjusted:
        # Create a new pattern dict (don't mutate the original)
        pattern = {**pattern, "zones": new_zones}

    return pattern


def _required_zones(intent):
    """Return the set of zone roles required for an intent, or None if flexible."""
    requirements = {
        "open": {"title"},
        "close": {"title"},
        "divide": {"title"},
        "visualize": {"chart"},
        "tabulate": {"table"},
    }
    return requirements.get(intent)


def _preferred_columns(intent, slide_spec):
    """Determine preferred column count from content."""
    if intent == "compare":
        return len(slide_spec.get("sides", []))
    if intent == "categorize":
        sides = slide_spec.get("sides", slide_spec.get("columns", []))
        return min(len(sides), 4)
    if intent == "evaluate":
        return len(slide_spec.get("options", []))
    if intent == "illustrate":
        return 2  # media + content
    return 1
