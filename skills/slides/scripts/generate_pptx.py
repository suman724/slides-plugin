#!/usr/bin/env python3
"""Generate an enterprise-quality PPTX from a JSON slide specification.

Usage:
    python3 generate_pptx.py --input spec.json --output presentation.pptx
    python3 generate_pptx.py --input spec.json  # outputs to ./presentation.pptx
    echo '<json>' | python3 generate_pptx.py --output presentation.pptx  # stdin
"""

import argparse
import json
import sys
import os

# Add scripts directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pptx import Presentation
from pptx.util import Inches

from design_system import load_theme, Grid
from layouts import LAYOUT_REGISTRY
from components import add_slide_footer


def validate_spec(spec):
    """Validate the JSON specification and return errors."""
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
            if "type" not in slide_spec:
                errors.append(f"Slide {i + 1}: missing 'type' field")
            elif slide_spec["type"] not in LAYOUT_REGISTRY:
                errors.append(
                    f"Slide {i + 1}: unknown type '{slide_spec['type']}'. "
                    f"Valid types: {', '.join(sorted(LAYOUT_REGISTRY.keys()))}"
                )

    return errors


def generate(spec):
    """Generate a PPTX presentation from a validated spec."""
    metadata = spec.get("metadata", {})
    slides_spec = spec.get("slides", [])

    # Load theme and grid
    theme = load_theme(metadata.get("theme", "corporate_blue"))
    grid = Grid()

    # Create presentation
    prs = Presentation()
    prs.slide_width = Inches(grid.slide_width)
    prs.slide_height = Inches(grid.slide_height)

    total_slides = len(slides_spec)

    for i, slide_spec in enumerate(slides_spec):
        slide_type = slide_spec["type"]
        layout_fn = LAYOUT_REGISTRY[slide_type]

        # Always use blank layout (index 6)
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)

        # Render the layout
        layout_fn(slide, slide_spec, theme, grid)

        # Add footer to all slides except title and closing
        if slide_type not in ("title", "closing", "section_divider"):
            add_slide_footer(slide, metadata, i + 1, total_slides, theme, grid)

    return prs


def main():
    parser = argparse.ArgumentParser(
        description="Generate enterprise-quality PPTX from JSON specification"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Path to JSON specification file (reads from stdin if omitted)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./presentation.pptx",
        help="Output PPTX file path (default: ./presentation.pptx)",
    )
    args = parser.parse_args()

    # Read spec
    try:
        if args.input:
            with open(args.input, "r") as f:
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

    # Use output_path from metadata if not specified via CLI
    output_path = args.output
    if output_path == "./presentation.pptx":
        output_path = spec.get("metadata", {}).get("output_path", output_path)

    # Generate
    prs = generate(spec)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    prs.save(output_path)
    print(f"Presentation saved to: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
