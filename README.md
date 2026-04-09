# Slides Skill for Claude Code

A Claude Code skill that generates enterprise-quality PowerPoint (PPTX) presentations from natural language. Visual styles are derived from a library of real enterprise presentation designs, and layouts are determined automatically from content semantics.

## Quick Start

### Install the skill

Copy the `slides/` directory to your Claude Code skills location:

```bash
# Personal (all projects)
cp -r slides/ ~/.claude/skills/slides/

# Or project-specific
cp -r slides/ .claude/skills/slides/
```

### Install Python dependency

```bash
pip3 install python-pptx
```

### Use it

In Claude Code, just ask:

```
/slides quarterly business review for Acme Corp, revenue $142M +18% YoY
```

Or provide more context:

```
/slides Create a strategy presentation about our cloud migration plan.
We're moving from on-prem to AWS over 18 months. Budget: $5M.
Key milestones: assessment (Q1), pilot (Q2), migration (Q3-Q4), optimization (Q1 next year).
Risks: downtime, data loss, team skill gaps.
```

Claude will generate a professional PPTX file with appropriate slide types, layouts, and styling.

## How It Works

1. **You describe the content** -- Claude analyzes your input and selects semantic intents (`explain`, `compare`, `measure`, `visualize`, etc.)
2. **Claude generates a JSON spec** -- a semantic description of each slide's content, not its visual layout
3. **The rendering engine takes over** -- resolves visual style from the style library, maps intents to layout patterns, renders shapes, and runs quality assurance checks
4. **You get a PPTX file** -- professional, well-formatted, ready to present

### 15 Semantic Intents

| Intent | Use For |
|---|---|
| `open` | Cover slide |
| `close` | Thank you / ending |
| `outline` | Agenda / table of contents |
| `divide` | Section break |
| `explain` | Bullet points |
| `compare` | Side-by-side (2 items) |
| `categorize` | 3+ parallel categories |
| `measure` | KPI dashboard (3-4 cards) |
| `visualize` | Charts (column, bar, line, pie, etc.) |
| `tabulate` | Data tables |
| `evaluate` | Pros/cons analysis |
| `sequence` | Timeline / roadmap |
| `emphasize` | Big number or notable quote |
| `illustrate` | Image + text |
| `summarize` | Key takeaways + call to action |

### Style Library

Visual styles (colors, fonts, spacing, decorative elements) are extracted from real enterprise PPTX templates using a preprocessing pipeline. The extracted patterns ship as `style_library.json` with the skill.

Style can be customized:
- `"mood": "professional"` -- conservative, clean (default)
- `"mood": "bold"` -- high-contrast, vibrant
- `"font": "Calibri"` -- match by font family

### Quality Assurance

Three-layer safety system ensures formatting quality:
1. **Overflow prevention** -- adjusts content/fonts/spacing before rendering
2. **Zone clamping** -- ensures shapes stay within slide boundaries
3. **Post-render validation** -- audits for overlaps and applies corrective fixes

## Testing

### Run the test suite

```bash
pip3 install pytest
python3 -m pytest tests/test_edge_cases.py -v
```

20 edge-case tests covering: bullet overflow, long titles, many metrics, wide/tall tables, chart categories, timeline milestones, compare options, unicode content, empty content, and all 15 intents with both moderate and heavy content.

### Generate a sample presentation

```bash
python3 slides/scripts/generate_pptx.py --input tests/sample_spec_v2.json --output sample.pptx
```

### Generate a visual gallery (all intents)

```bash
python3 tests/generate_gallery.py
open tests/gallery/gallery_all_intents.pptx
```

### Test with Claude Code

After installing the skill, try these in Claude Code:

**Minimal input** (Claude generates everything):
```
/slides quarterly business review
```

**With data points**:
```
/slides quarterly review: revenue $142M, growth 18%, churn 4.2%, ARR $568M
```

**Specific deck type**:
```
/slides product launch pitch deck for an AI-powered analytics platform
```

**With full context** (paste a document or outline, then):
```
/slides create a presentation from the above content
```

## Project Structure

```
slides-plugin/
├── slides/                  # THE SKILL -- copy this to ~/.claude/skills/
│   ├── SKILL.md             # Skill definition (Claude's instructions)
│   ├── references/          # Reference docs for Claude
│   │   ├── semantic-content-model.md
│   │   ├── intent-reference.md
│   │   ├── style-guide.md
│   │   └── content-guidelines.md
│   └── scripts/             # Rendering engine
│       ├── generate_pptx.py      # Entry point
│       ├── style_resolver.py     # Palette/typography resolution
│       ├── intent_mapper.py      # Intent -> layout pattern
│       ├── overflow.py           # Pre-render overflow prevention
│       ├── layout_engine.py      # Zone-based rendering
│       ├── shape_renderer.py     # Low-level PPTX shapes
│       ├── layout_validator.py   # Post-render validation + fixes
│       └── style_library.json    # Extracted design patterns
├── pipeline/                # Build-time: style library extraction
│   ├── manifest.yaml        # 52 PPTX source URLs
│   ├── download.py          # Download templates
│   ├── extract.py           # Extract design patterns
│   ├── aggregate.py         # Cluster into style library
│   └── run_pipeline.sh      # Run full pipeline
├── tests/                   # Test suite
│   ├── test_edge_cases.py   # 20 edge-case tests
│   ├── sample_spec_v2.json  # Sample semantic spec
│   └── generate_gallery.py  # Visual gallery generator
├── DESIGN.md                # Full design document
└── README.md                # This file
```

## Rebuilding the Style Library

To update the style library with new source templates:

1. Add PPTX files to `pipeline/raw/` (download manually or via `pipeline/download.py`)
2. Run extraction: `python3 pipeline/extract.py --all`
3. Run aggregation: `python3 pipeline/aggregate.py`
4. The updated `style_library.json` is written to `slides/scripts/`

## License

Style library patterns are extracted from openly-licensed templates (CC-BY 4.0 from SlidesCarnival, free-tier from Slidesgo/SlideEgg/SlideHunter). See `pipeline/manifest.yaml` for full attribution.
