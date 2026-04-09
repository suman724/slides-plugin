#!/usr/bin/env python3
"""Generate an enterprise-quality PPTX from a semantic JSON specification.

v2 pipeline: validate -> resolve style -> map intents -> render slides.

Usage:
    python3 generate_pptx.py --input spec.json --output presentation.pptx
    python3 generate_pptx.py --input spec.json  # outputs to ./presentation.pptx
    echo '<json>' | python3 generate_pptx.py --output presentation.pptx
"""

import argparse
import json
import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pptx import Presentation
from pptx.util import Inches

from style_resolver import resolve_style
from intent_mapper import resolve_layout
from overflow import apply_overflow_rules
from layout_engine import render_slide
from layout_validator import validate_and_fix


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

VALID_INTENTS = {
    "open", "close", "outline", "divide", "explain", "compare",
    "categorize", "measure", "visualize", "tabulate", "evaluate",
    "sequence", "emphasize", "illustrate", "summarize",
}


def validate_spec(spec):
    """Validate the semantic JSON specification."""
    errors = []

    if "metadata" not in spec:
        errors.append("Missing 'metadata' section")

    if "slides" not in spec:
        errors.append("Missing 'slides' section")
    elif not isinstance(spec["slides"], list):
        errors.append("'slides' must be a list")
    elif len(spec["slides"]) == 0:
        errors.append("'slides' list is empty")
    else:
        for i, slide_spec in enumerate(spec["slides"]):
            intent = slide_spec.get("intent")
            if not intent:
                errors.append(f"Slide {i + 1}: missing 'intent' field")
            elif intent not in VALID_INTENTS:
                errors.append(
                    f"Slide {i + 1}: unknown intent '{intent}'. "
                    f"Valid: {', '.join(sorted(VALID_INTENTS))}"
                )

    return errors


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(spec):
    """Generate a PPTX from a semantic specification.

    Pipeline: resolve style -> for each slide: map intent -> overflow prevention
    -> render -> after all slides: validate and fix.
    """
    metadata = spec.get("metadata", {})
    slides_spec = spec.get("slides", [])

    # Resolve style from library
    style = resolve_style(metadata)

    # Create presentation
    prs = Presentation()
    prs.slide_width = Inches(style.slide_width_inches)
    prs.slide_height = Inches(style.slide_height_inches)

    warnings = []

    # Layer 1: Overflow prevention + Layer 2: Rendering
    # Process slides, collecting any extra slides from content splitting
    all_slide_specs = []
    for slide_spec in slides_spec:
        intent = slide_spec.get("intent", "explain")
        layout_pattern, content_mapping, adapted_intent = resolve_layout(intent, slide_spec)

        # Layer 1: Overflow prevention
        overflow_result = apply_overflow_rules(slide_spec, layout_pattern, style)
        warnings.extend(overflow_result.warnings)

        # The main slide (possibly adjusted)
        all_slide_specs.append((overflow_result.adjusted_spec, adapted_intent))

        # Extra slides from content splitting
        for extra_spec in overflow_result.extra_slides:
            extra_spec["intent"] = adapted_intent
            all_slide_specs.append((extra_spec, adapted_intent))

        if adapted_intent != intent:
            warnings.append(
                f"Slide: intent '{intent}' adapted to '{adapted_intent}'"
            )

    total_slides = len(all_slide_specs)

    for i, (slide_spec, adapted_intent) in enumerate(all_slide_specs):
        # Re-resolve layout for potentially modified spec
        layout_pattern, content_mapping, _ = resolve_layout(adapted_intent, slide_spec)

        # Create blank slide
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)

        # Layer 2: Render
        render_slide(
            slide, adapted_intent, layout_pattern, content_mapping, style,
            metadata, i + 1, total_slides,
        )

    # Layer 3: Validate and fix
    prs, validation_issues = validate_and_fix(prs)

    for issue in validation_issues:
        prefix = "WARNING" if issue.auto_fixed else "ERROR"
        if issue.auto_fixed:
            warnings.append(f"{prefix}: {issue.description} (auto-fixed)")
        elif issue.severity == "error":
            warnings.append(f"ERROR: {issue.description}")

    return prs, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate enterprise-quality PPTX from semantic JSON specification"
    )
    parser.add_argument("--input", "-i", type=str, help="JSON spec file path (stdin if omitted)")
    parser.add_argument("--output", "-o", type=str, default="./presentation.pptx", help="Output path")
    args = parser.parse_args()

    # Read spec
    try:
        if args.input:
            with open(args.input) as f:
                spec = json.load(f)
        else:
            spec = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found - {args.input}", file=sys.stderr)
        sys.exit(1)

    # Validate
    errors = validate_spec(spec)
    if errors:
        print("Validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    # Use output_path from metadata if not overridden
    output_path = args.output
    if output_path == "./presentation.pptx":
        output_path = spec.get("metadata", {}).get("output_path", output_path)

    # Generate
    prs, warnings = generate(spec)

    # Report warnings
    for w in warnings:
        print(f"  {w}")

    # Save
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    prs.save(output_path)
    print(f"Presentation saved to: {os.path.abspath(output_path)}")
    print(f"  Slides: {len(spec['slides'])}")


if __name__ == "__main__":
    main()
