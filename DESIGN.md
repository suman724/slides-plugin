# Design Doc: `/slides` -- Enterprise PPTX Presentation Generator

## Context

We need a Claude Code skill (slash command) that generates enterprise-quality PowerPoint (PPTX) presentations. Users provide context/topic; the skill structures content, augments it with LLM-generated material when needed, and produces a professional PPTX file.

The visual quality and layout intelligence come from **real enterprise presentations** -- not hardcoded themes or predefined layouts. At build time, a preprocessing pipeline downloads ~50 high-quality openly-licensed PPTX files, extracts design patterns (colors, fonts, layouts, spacing, decorative elements), and ships them as a JSON style library. At runtime, the plugin dynamically determines layouts based on content semantics.

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Plugin type | Claude Code Skill (slash command) | Integrates naturally with Claude's conversation flow |
| Language | Python + `python-pptx` | Most mature PPTX library with rich low-level control |
| Visual quality source | Extracted from ~50 real PPTX files | Real-world design quality, not hand-tuned constants |
| Layout determination | Hybrid: discovered from data + structural fallbacks | Pipeline discovers patterns from real files; 4 predefined fallbacks guarantee the plugin always works |
| Content model | Semantic intents (what), not visual types (how) | Clean separation: Claude describes content, engine handles presentation |
| Style library | JSON, built offline, shipped with plugin | No runtime downloads; fast, reliable, deterministic |

---

## Architecture Overview

### Two-Phase System

**Phase A: Build Time (preprocessing pipeline)**
```
manifest.yaml (50 PPTX source URLs)
        |
        v
  download.py --> raw PPTX files
        |
        v
  extract.py --> per-file style profiles (JSON)
        |
        v
  aggregate.py --> clustered style library (JSON)
        |
        v
  style_library.json (ships with plugin)
```

**Phase B: Runtime (when user invokes /slides)**
```
User invokes /slides <topic or context>
        |
        v
  Claude analyzes content, picks semantic intents
        |
        v
  Claude generates semantic JSON specification
        |
        v
  generate_pptx.py:
    1. style_resolver.py  --> resolves palette + typography from library
    2. intent_mapper.py   --> maps each intent to a layout pattern
    3. layout_engine.py   --> renders content into positioned shapes
    4. shape_renderer.py  --> low-level PPTX shape creation
        |
        v
  User gets professional presentation file
```

### Core Principle: Separation of Concerns

| Layer | Responsibility | Knows About |
|---|---|---|
| **Claude (LLM)** | Content strategy, augmentation, intent selection | What information to present, not how |
| **Style Resolver** | Picking colors, fonts, spacing | Style library palettes and typography |
| **Intent Mapper** | Choosing layout pattern for each slide | Content structure + available layout patterns |
| **Layout Engine** | Positioning shapes on the slide | Zone geometries from layout patterns |
| **Shape Renderer** | Drawing text, charts, tables, shapes | python-pptx API |

---

## File Structure

```
slides-plugin/
├── pipeline/                                # Build-time preprocessing
│   ├── manifest.yaml                        # ~50 PPTX source URLs + metadata
│   ├── download.py                          # Downloads PPTX files to raw/
│   ├── extract.py                           # Extracts per-file style profiles
│   ├── aggregate.py                         # Clusters profiles into style library
│   ├── run_pipeline.sh                      # Orchestrates: download -> extract -> aggregate
│   ├── requirements.txt                     # Pipeline deps (requests, numpy, pyyaml, lxml)
│   ├── raw/                                 # Downloaded PPTX files (gitignored)
│   └── profiles/                            # Per-file JSON profiles (gitignored)
│
├── skills/
│   └── slides/
│       ├── SKILL.md                         # Skill definition + orchestration
│       ├── references/
│       │   ├── semantic-content-model.md    # Full semantic JSON model docs
│       │   ├── intent-reference.md          # All intents with examples
│       │   ├── style-guide.md              # Available palettes and moods
│       │   └── content-guidelines.md        # Deck patterns + content rules
│       └── scripts/
│           ├── generate_pptx.py             # Entry point: validate -> resolve -> map -> render
│           ├── style_resolver.py            # Resolves style preferences from library
│           ├── intent_mapper.py             # Maps semantic intents to layout patterns
│           ├── layout_engine.py             # Generic renderer: zones + content -> shapes
│           ├── shape_renderer.py            # Low-level shape/text/chart/table rendering
│           └── style_library.json           # Build artifact from pipeline
│
├── tests/
│   ├── test_generate_pptx.py
│   ├── test_style_resolver.py
│   ├── test_intent_mapper.py
│   ├── test_layout_engine.py
│   ├── test_pipeline.py
│   ├── generate_gallery.py
│   └── sample_spec.json
│
├── requirements.txt                         # Runtime: python-pptx
├── DESIGN.md                                # This file
└── .gitignore                               # Includes pipeline/raw/, pipeline/profiles/
```

---

## Preprocessing Pipeline

### Source Manifest

The pipeline starts with a curated `manifest.yaml` listing ~50 PPTX sources:

```yaml
sources:
  # SlidesCarnival -- CC-BY 4.0, high quality, PPTX format
  - id: "sc-aurora"
    url: "https://www.slidescarnival.com/aurora-template/12345"
    license: "CC-BY-4.0"
    attribution: "SlidesCarnival"
    category: "corporate"
    tags: ["blue", "professional", "gradient"]

  # Slidesgo -- free tier, PPTX format
  - id: "sg-modern-pitch"
    url: "https://slidesgo.com/theme/modern-pitch"
    license: "free-tier"
    attribution: "Slidesgo"
    category: "creative"
    tags: ["bold", "startup", "colorful"]

  # SlideEgg -- free, PPTX format
  - id: "se-annual-report"
    url: "https://www.slideegg.com/template/annual-report"
    license: "free"
    attribution: "SlideEgg"
    category: "corporate"
    tags: ["formal", "data-heavy"]

  # Public company investor decks
  - id: "apple-ir-q3-2025"
    url: "https://investor.apple.com/..."
    license: "public-document"
    attribution: "Apple Inc."
    category: "corporate"
    tags: ["minimal", "premium"]

  # Government / public domain
  - id: "usgov-template-01"
    url: "https://..."
    license: "public-domain"
    attribution: "US Government"
    category: "formal"
    tags: ["conservative", "accessible"]
```

**Sourcing strategy for ~50 files:**

| Source | Count | License | Format | Quality |
|---|---|---|---|---|
| SlidesCarnival | 15-20 | CC-BY 4.0 | PPTX | High |
| Slidesgo | 10-15 | Free tier | PPTX | High |
| SlideEgg | 5-10 | Free | PPTX | High |
| SlideHunter | 5-10 | Free | PPTX | Medium-High |
| Public company IR decks | 5-10 | Public docs | PPTX/PDF | Very High |
| Government/public domain | 3-5 | Public domain | PPTX | Medium |

### Extraction Pipeline

**`extract.py`** analyzes each PPTX file and produces a per-file JSON profile:

1. **Color extraction**: Samples all RGB colors from shape fills, text runs, line colors. Parses `theme1.xml` via `lxml` to extract the 12 theme color slots (dk1, lt1, dk2, lt2, accent1-6). Identifies gradient stop colors.

2. **Typography extraction**: Records every `(font_name, size_pt, bold, italic)` combination and its frequency. Infers hierarchy roles by size: largest bold = display, next bold = heading, most common regular = body, smallest = caption.

3. **Layout extraction**: For each slide, records all shape positions as **proportional coordinates** (0.0-1.0 relative to slide dimensions). Clusters shapes into zones (title zone: top 20%, content zone: middle 60%, footer zone: bottom 15%). Detects column count by finding shapes at similar Y positions with distinct X positions.

4. **Spacing extraction**: Measures margins (smallest left/top edges), gutter widths (gaps between horizontally adjacent shapes), paragraph spacing.

5. **Decorative element extraction**: Identifies non-content shapes (no text, not images/charts): thin rectangles = accent bars, full-width rectangles = bands, circles, rounded rectangles. Records proportional positions and fill colors.

6. **Background extraction**: Records slide background fill type (solid/gradient) and colors.

### Aggregation

**`aggregate.py`** clusters all per-file profiles into the final style library:

1. **Color palette clustering**: Groups palettes by hue similarity (LAB color space distance). Identifies ~15-20 distinct palettes. Tags by mood: professional, bold, warm, minimal, dark.

2. **Typography pattern clustering**: Groups font hierarchies by similarity. Most enterprise templates use a small number of patterns (~5-8).

3. **Layout pattern clustering**: Groups slides by structural signature (zone count, column count, decorative elements). Produces ~12-15 canonical layout patterns.

4. **Decorative pattern extraction**: Identifies the 8-10 most common decorative patterns across all files.

---

## Style Library Format

The build artifact shipped with the plugin. All positions are proportional (0.0-1.0) for reusability across slide dimensions.

### Palettes

```json
{
  "palettes": [
    {
      "id": "corporate-navy",
      "mood": "professional",
      "temperature": "cool",
      "source_ids": ["sc-aurora", "sh-business-01"],
      "colors": {
        "primary": "#1B3A6B",
        "secondary": "#2E5C9E",
        "accent": "#E8913A",
        "accent_alt": "#3A8F6E",
        "text_primary": "#1A1A1A",
        "text_secondary": "#4A4A4A",
        "text_on_dark": "#FFFFFF",
        "background": "#FFFFFF",
        "background_alt": "#F0F4F8",
        "positive": "#2D8F5E",
        "negative": "#C0392B"
      },
      "chart_colors": ["#1B3A6B", "#E8913A", "#3A8F6E", "#2E5C9E", "#C0392B", "#6C5B7B"],
      "gradient_pairs": [["#1B3A6B", "#2E5C9E"]]
    },
    {
      "id": "warm-terracotta",
      "mood": "approachable",
      "temperature": "warm",
      "source_ids": ["sc-sahara", "sg-earth-tones"],
      "colors": {
        "primary": "#8B4513",
        "secondary": "#D2691E",
        "accent": "#DAA520",
        "...": "..."
      }
    }
  ]
}
```

### Typography Patterns

```json
{
  "typography_patterns": [
    {
      "id": "calibri-standard",
      "font_family": "Calibri",
      "fallback": "Arial",
      "source_ids": ["sc-aurora", "se-annual-report"],
      "hierarchy": {
        "display":    {"size_pt": 36, "bold": true},
        "title":      {"size_pt": 28, "bold": true},
        "heading":    {"size_pt": 20, "bold": true},
        "body":       {"size_pt": 14, "bold": false},
        "body_small": {"size_pt": 12, "bold": false},
        "caption":    {"size_pt": 10, "bold": false},
        "metric":     {"size_pt": 40, "bold": true},
        "footer":     {"size_pt": 8,  "bold": false}
      }
    }
  ]
}
```

### Layout Patterns: Hybrid Approach

Layout patterns come from two sources, with discovered patterns taking priority over fallbacks.

#### Source 1: Structural Fallbacks (predefined)

Some layouts exist because of their **function**, not their visual style. No clustering algorithm will "discover" that a deck needs an opening slide. These 4 patterns are hardcoded as minimum-viable fallbacks:

| Fallback | Purpose | Why Predefined |
|---|---|---|
| `fallback-cover` | Opening/cover slide | Every deck needs one; structural necessity |
| `fallback-close` | Closing/thank-you slide | Every deck needs one; structural necessity |
| `fallback-divider` | Section break | Navigational structure, not visual style |
| `fallback-content` | Title + bullet list | The universal workhorse; must always be available |

These ensure the plugin works even with an empty style library. They use sensible default proportional coordinates:

```json
{
  "structural_fallbacks": [
    {
      "id": "fallback-cover",
      "purpose": "opening",
      "background_type": "gradient",
      "zones": [
        {"role": "title",    "bounds_pct": {"left": 0.10, "top": 0.27, "width": 0.80, "height": 0.16}},
        {"role": "subtitle", "bounds_pct": {"left": 0.10, "top": 0.44, "width": 0.80, "height": 0.08}}
      ]
    },
    {
      "id": "fallback-close",
      "purpose": "closing",
      "background_type": "gradient",
      "zones": [
        {"role": "title",    "bounds_pct": {"left": 0.10, "top": 0.29, "width": 0.80, "height": 0.13}},
        {"role": "subtitle", "bounds_pct": {"left": 0.10, "top": 0.45, "width": 0.80, "height": 0.08}},
        {"role": "contact",  "bounds_pct": {"left": 0.10, "top": 0.57, "width": 0.80, "height": 0.05}}
      ]
    },
    {
      "id": "fallback-divider",
      "purpose": "section_break",
      "background_type": "solid",
      "zones": [
        {"role": "panel",    "bounds_pct": {"left": 0.0,   "top": 0.0,  "width": 0.338, "height": 1.0}},
        {"role": "number",   "bounds_pct": {"left": 0.038, "top": 0.27, "width": 0.263, "height": 0.20}},
        {"role": "title",    "bounds_pct": {"left": 0.39,  "top": 0.29, "width": 0.555, "height": 0.13}},
        {"role": "subtitle", "bounds_pct": {"left": 0.39,  "top": 0.47, "width": 0.555, "height": 0.08}}
      ]
    },
    {
      "id": "fallback-content",
      "purpose": "general",
      "background_type": "solid",
      "zones": [
        {"role": "title",   "bounds_pct": {"left": 0.056, "top": 0.053, "width": 0.888, "height": 0.107}},
        {"role": "content", "bounds_pct": {"left": 0.071, "top": 0.187, "width": 0.858, "height": 0.68}}
      ]
    }
  ]
}
```

#### Source 2: Discovered Patterns (from pipeline)

The preprocessing pipeline analyzes ~50 real PPTX files and **discovers** layout patterns through geometric clustering. The actual patterns, their count, and their zone structures are **output of the pipeline, not predefined**.

**How discovery works:**

1. **Per-slide feature extraction**: For each slide in each source file, extract a "structural signature":
   - Number of content zones (text boxes, charts, tables, images)
   - Zone bounding boxes as proportional coordinates
   - Column count (shapes at similar Y with distinct X positions)
   - Background type (solid, gradient, image)
   - Presence of decorative elements (accent bars, shapes without text)

2. **Clustering**: Group slides across all source files by structural signature similarity. Use distance metric based on:
   - Zone count match
   - Bounding box overlap (IoU -- Intersection over Union)
   - Column structure match
   - Background type match

3. **Cluster representative**: For each cluster, compute the **median** bounding boxes across all member slides. This produces the canonical zone positions for the pattern.

4. **Labeling**: Each discovered pattern gets:
   - An auto-generated `id` (e.g., `discovered-2col-v1`, `discovered-grid-2x2`)
   - A `purpose` tag inferred from content analysis (e.g., slides with charts get purpose `visualize`)
   - A `source_count` showing how many source slides matched this pattern
   - A `confidence` score based on cluster tightness

**What we expect to discover** (but don't assume):
- Multiple column variants (2-col equal, 2-col 60/40, 3-col)
- Chart + annotation patterns
- Metric card grids (row of 3, row of 4, 2x2 grid)
- Image + text splits (left/right, top/bottom)
- Full-bleed backgrounds vs. minimal backgrounds
- Patterns we haven't anticipated

**What we might NOT find** (handled by fallbacks):
- Timeline-specific layouts (rare in template files)
- KPI-specific card arrangements (usually just rounded rectangles in a column layout)

#### Resolution Priority

When the intent mapper needs a layout for a given intent:

```
1. Look for a discovered pattern with matching purpose
   - If multiple matches, prefer higher source_count (more common = more tested)
   - If still tied, prefer higher confidence
2. If no discovered match, fall back to structural fallback
3. If no fallback matches (shouldn't happen), use fallback-content as last resort
```

This means:
- If the pipeline discovers a beautiful cover layout from 30+ real presentations, it overrides `fallback-cover`
- If no pipeline-discovered layout fits a `visualize` intent, `fallback-content` is used with the chart rendered into its content zone
- The plugin always works, even with zero discovered patterns

#### Style Library Format for Discovered Patterns

```json
{
  "discovered_patterns": [
    {
      "id": "discovered-2col-equal-v1",
      "purpose": "compare",
      "source_count": 38,
      "confidence": 0.91,
      "source_ids": ["sc-aurora", "sg-modern-pitch", "..."],
      "background_type": "solid",
      "zones": [
        {"role": "title",     "bounds_pct": {"left": 0.06, "top": 0.05, "width": 0.88, "height": 0.11}},
        {"role": "col_left",  "bounds_pct": {"left": 0.06, "top": 0.19, "width": 0.43, "height": 0.68}},
        {"role": "col_right", "bounds_pct": {"left": 0.52, "top": 0.19, "width": 0.43, "height": 0.68}}
      ],
      "decorative": ["accent_bar_below_title"]
    },
    {
      "id": "discovered-chart-annotated-v1",
      "purpose": "visualize",
      "source_count": 24,
      "confidence": 0.85,
      "source_ids": ["se-annual-report", "..."],
      "background_type": "solid",
      "zones": [
        {"role": "title",      "bounds_pct": {"left": 0.06, "top": 0.05, "width": 0.88, "height": 0.11}},
        {"role": "chart",      "bounds_pct": {"left": 0.07, "top": 0.19, "width": 0.86, "height": 0.58}},
        {"role": "annotation", "bounds_pct": {"left": 0.07, "top": 0.80, "width": 0.86, "height": 0.06}}
      ],
      "decorative": []
    }
  ]
}
```

The `"..."` entries above are illustrative. **The actual patterns are TBD until the pipeline runs on real data.**

### Decorative Elements

```json
{
  "decorative_elements": {
    "accent_bar_below_title": {
      "shape": "rectangle",
      "relative_to": "title_zone_bottom",
      "offset_pct": {"top": 0.007},
      "size_pct": {"width": 0.113, "height": 0.005},
      "fill_role": "accent"
    },
    "accent_stripe_left": {
      "shape": "rectangle",
      "position_pct": {"left": 0.045, "top": 0.24},
      "size_pct": {"width": 0.006, "height": 0.467},
      "fill_role": "accent"
    },
    "footer_band": {
      "shape": "rectangle",
      "position_pct": {"left": 0.0, "top": 0.893},
      "size_pct": {"width": 1.0, "height": 0.107},
      "fill_role": "primary"
    },
    "footer_separator": {
      "shape": "line",
      "position_pct": {"left": 0.056, "top": 0.92},
      "size_pct": {"width": 0.888, "height": 0.001},
      "fill_role": "text_secondary"
    },
    "rounded_card_bg": {
      "shape": "rounded_rectangle",
      "fill_role": "background_alt"
    },
    "connector_line": {
      "shape": "rectangle",
      "fill_role": "text_secondary",
      "size_pct": {"height": 0.005}
    },
    "circle_markers": {
      "shape": "oval",
      "fill_role": "accent",
      "size_pct": {"width": 0.034, "height": 0.04}
    }
  }
}
```

---

## Semantic Content Model

The fundamental change: Claude describes **what** the content is, not **how** to lay it out. Field names are domain-language (`advantages`, `metrics`, `steps`), not visual-language (`left_column`, `card`, `green_text`). Intent values are verbs (`compare`, `measure`, `visualize`), not nouns (`two_column`, `key_metrics`, `chart`).

### Top-Level Structure

```json
{
  "metadata": {
    "title": "Q3 2026 Strategic Review",
    "subtitle": "Board of Directors Presentation",
    "author": "Strategy Team",
    "company": "Acme Corp",
    "date": "April 2026",
    "confidentiality": "Confidential",
    "style": {
      "palette": "corporate-navy",
      "typography": "calibri-standard"
    }
  },
  "slides": [ ... ]
}
```

The `style` object can specify exact IDs or a `mood` keyword:
- `{"palette": "corporate-navy"}` -- exact lookup
- `{"mood": "professional"}` -- engine picks best matching palette
- omitted entirely -- engine uses default

### Semantic Intents

| Intent | Meaning | Looks for purpose | Fallback |
|---|---|---|---|
| `open` | Opening/cover slide | `opening` | `fallback-cover` |
| `close` | Thank you / end | `closing` | `fallback-close` |
| `outline` | Table of contents | `outline` | `fallback-content` |
| `divide` | Section break | `section_break` | `fallback-divider` |
| `explain` | Narrative information | `explain` | `fallback-content` |
| `compare` | Side-by-side comparison | `compare` | `fallback-content` |
| `categorize` | 3+ parallel categories | `categorize` | `fallback-content` |
| `measure` | KPI/metric dashboard | `measure` | `fallback-content` |
| `visualize` | Chart/graph | `visualize` | `fallback-content` |
| `tabulate` | Detailed data table | `tabulate` | `fallback-content` |
| `evaluate` | Pros/cons analysis | `evaluate` | `fallback-content` |
| `sequence` | Timeline/roadmap | `sequence` | `fallback-content` |
| `emphasize` | Big number or quote | `emphasize` | `fallback-content` |
| `illustrate` | Image + text | `illustrate` | `fallback-content` |
| `summarize` | Key takeaways | `summarize` | `fallback-content` |

The "Looks for purpose" column shows what `purpose` tag the mapper searches for in discovered patterns. If no discovered pattern matches, the fallback is used.

**Content-adaptive overrides**: The intent mapper can adjust layout based on content:
- `compare` with 3 sides -> look for `categorize` purpose instead
- `explain` with only 1 short point -> look for `emphasize` purpose instead
- `measure` with 6 metrics -> split across 2 slides

### Slide Specification Examples

**Opening:**
```json
{"intent": "open", "title": "Q3 2026 Strategic Review", "subtitle": "Prepared for the Board"}
```

**Outline:**
```json
{
  "intent": "outline",
  "title": "Agenda",
  "items": [
    {"text": "Market Overview", "detail": "Industry trends and landscape"},
    {"text": "Financial Performance", "detail": "Revenue, margins, and KPIs"}
  ]
}
```

**Explain:**
```json
{
  "intent": "explain",
  "title": "Key Market Trends",
  "points": [
    {"text": "TAM grew 12% YoY to $4.2B", "subpoints": [
      "Enterprise segment accounts for 65% of growth",
      "SMB segment showing early recovery"
    ]},
    {"text": "Competitor X launched adjacent product in Q2"},
    {"text": "Regulatory changes expected in H2 2026"}
  ]
}
```

**Compare:**
```json
{
  "intent": "compare",
  "title": "Revenue vs. Plan",
  "sides": [
    {"heading": "Performance", "points": ["Revenue: $142M (+18%)", "Margin: 72%"]},
    {"heading": "Commentary", "points": ["Pipeline strong", "SMB churn at 4.2%"]}
  ]
}
```

**Measure:**
```json
{
  "intent": "measure",
  "title": "Key Performance Indicators",
  "metrics": [
    {"label": "ARR", "value": "$568M", "change": "+18%", "trend": "up"},
    {"label": "NRR", "value": "118%", "change": "+3pp", "trend": "up"},
    {"label": "Churn", "value": "4.2%", "change": "+0.8pp", "trend": "down"}
  ]
}
```

**Visualize:**
```json
{
  "intent": "visualize",
  "title": "Revenue by Quarter",
  "chart": {
    "type": "column_clustered",
    "categories": ["Q1", "Q2", "Q3"],
    "series": [{"name": "Revenue ($M)", "values": [128, 135, 142]}]
  },
  "note": "Q3 revenue within 2% of target"
}
```

**Evaluate:**
```json
{
  "intent": "evaluate",
  "title": "Strategic Options",
  "options": [
    {
      "heading": "Option A: Organic Growth",
      "advantages": ["Lower risk", "Preserves cash"],
      "challenges": ["Slower capture", "Competitor gap widens"]
    },
    {
      "heading": "Option B: Acquisition",
      "advantages": ["Immediate share", "Tech synergies"],
      "challenges": ["Integration risk", "$200M capital"]
    }
  ]
}
```

**Sequence:**
```json
{
  "intent": "sequence",
  "title": "Implementation Roadmap",
  "steps": [
    {"when": "Q4 2026", "what": "Board Approval", "detail": "Final direction decision"},
    {"when": "Q1 2027", "what": "Execution Begins", "detail": "Team formation"}
  ]
}
```

**Emphasize (big number):**
```json
{
  "intent": "emphasize",
  "title": "Market Opportunity",
  "emphasis": {
    "type": "number",
    "value": "$4.2B",
    "label": "Total Addressable Market",
    "context": "Growing at 12% annually"
  }
}
```

**Emphasize (quote):**
```json
{
  "intent": "emphasize",
  "emphasis": {
    "type": "quote",
    "text": "The best way to predict the future is to create it.",
    "attribution": "Peter Drucker"
  }
}
```

**Summarize:**
```json
{
  "intent": "summarize",
  "title": "Key Takeaways",
  "takeaways": [
    "Q3 performance strong despite headwinds",
    "Enterprise pipeline robust; SMB churn needs action",
    "Board decision needed by Q4 2026"
  ],
  "action": "Approve formation of Strategic Evaluation Committee"
}
```

---

## Runtime Engine

### Style Resolver (`style_resolver.py`)

Resolves the `metadata.style` object into a concrete `ResolvedStyle` dataclass:

1. If `palette` is an exact ID (e.g., `"corporate-navy"`) -- look up directly
2. If `mood` is given (e.g., `"professional"`) -- filter palettes by mood, pick first match
3. If nothing given -- default to first palette
4. Same for typography
5. Returns `ResolvedStyle` with all colors, fonts, and spacing as concrete values

### Intent Mapper (`intent_mapper.py`)

Maps each slide's `intent` to a layout pattern using the hybrid resolution strategy:

```python
# Maps intents to the purpose tags they search for in discovered patterns
INTENT_TO_PURPOSE = {
    "open":        "opening",
    "close":       "closing",
    "outline":     "outline",
    "divide":      "section_break",
    "explain":     "explain",
    "compare":     "compare",
    "categorize":  "categorize",
    "measure":     "measure",
    "visualize":   "visualize",
    "tabulate":    "tabulate",
    "evaluate":    "evaluate",
    "sequence":    "sequence",
    "emphasize":   "emphasize",
    "illustrate":  "illustrate",
    "summarize":   "summarize",
}

# Fallbacks when no discovered pattern matches
INTENT_TO_FALLBACK = {
    "open":    "fallback-cover",
    "close":   "fallback-close",
    "divide":  "fallback-divider",
    # Everything else falls back to fallback-content
}

def resolve_layout(intent, style_library):
    purpose = INTENT_TO_PURPOSE[intent]
    # 1. Search discovered patterns by purpose (prefer higher source_count)
    # 2. If no match, use structural fallback
    # 3. Last resort: fallback-content
```

Also assigns content fields to zone roles (e.g., `sides[0]` -> `col_left`, `sides[1]` -> `col_right`).

### Layout Engine (`layout_engine.py`)

A single generic renderer replaces 16 hardcoded layout functions:

1. Apply background (solid or gradient based on layout pattern)
2. For each zone in the layout pattern:
   - Convert proportional bounds to absolute inches
   - Look up which content field maps to this zone
   - Dispatch to the appropriate shape renderer
3. Render decorative elements
4. Render footer (if not opening/closing)

Zone rendering dispatches by role:

| Zone Role | Renders |
|---|---|
| `title` | Text box with display/title font |
| `subtitle` | Text box with body font |
| `content` | Bullet list |
| `col_left`, `col_right`, `col_1`-`col_3` | Heading + bullet list within bounds |
| `chart` | Chart via python-pptx chart API |
| `table` | Table via python-pptx table API |
| `cards` | N metric cards evenly spaced |
| `timeline` | Milestone markers along connector line |
| `statement` | Large centered text (number or quote) |
| `media` | Image or placeholder |
| `list` | Numbered items |
| `callout` | Accent-colored card with text |
| `panel` | Solid-fill rectangle |
| `number` | Large section number |
| `annotation` | Small caption text |

### Shape Renderer (`shape_renderer.py`)

Consolidates all low-level python-pptx rendering. Key functions:
- `render_text(slide, text, bounds, font_role, style)`
- `render_bullets(slide, points, bounds, style)` -- handles nested subpoints
- `render_chart(slide, chart_spec, bounds, style)`
- `render_table(slide, table_spec, bounds, style)`
- `render_metric_cards(slide, metrics, bounds, style)`
- `render_timeline(slide, steps, bounds, style)`
- `render_decorative(slide, element_spec, style, slide_dims)`
- `render_background(slide, bg_type, style, slide_dims)`
- `render_footer(slide, metadata, page_num, total, style, slide_dims)`

---

## LLM Content Augmentation Strategy

Same three levels as before, but Claude now thinks in semantic intents:

| Level | Input | Claude's Role |
|---|---|---|
| **Minimal** | `/slides quarterly review` | Generate full deck with intents: open, outline, divide, explain, measure, visualize, summarize, close |
| **Structured** | `/slides quarterly review: revenue $142M` | Use data as anchors, pick appropriate intents |
| **Detailed** | Full outline or document | Structure faithfully, add open/close if missing |

**Content rules:**
- Always start with `open`, end with `summarize` or `close`
- 3+ sections -> add `outline` after `open` + `divide` before each section
- Limit bullet points to 5-7 per slide
- Cap at 20 slides
- Use `measure` when 3-4 KPIs available
- Use `visualize` when time-series data present
- Use `evaluate` when presenting options

---

## Implementation Phases

### Phase 1: Preprocessing Pipeline
Build `pipeline/` -- manifest, download, extract, aggregate. Start with 10 SlidesCarnival files (clearest licensing). Output first `style_library.json`.

### Phase 2: Style Resolver
Implement `style_resolver.py` -- loads library, resolves palette/typography by ID or mood. Replaces hardcoded `design_system.py`.

### Phase 3: Semantic Content Model + Intent Mapper
Define new JSON schema. Implement `intent_mapper.py`. Write reference docs. Update `sample_spec.json`.

### Phase 4: Layout Engine + Shape Renderer
Build generic `layout_engine.py` (single renderer for all layouts). Refactor current rendering code into `shape_renderer.py`.

### Phase 5: SKILL.md + Reference Docs
Rewrite skill definition for semantic model. Update all reference docs.

### Phase 6: Testing + Gallery + Polish
Update tests, generate gallery with multiple palettes, visual QA, cleanup.

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| PPTX source URLs break over time | Commit downloaded files (or checksums); pipeline re-downloads only on demand |
| License ambiguity on some sources | Start with SlidesCarnival (CC-BY 4.0 is unambiguous); add others incrementally |
| Extraction quality varies by file | Manual curation step after aggregation; bad profiles can be excluded |
| Style library grows stale | Re-run pipeline periodically with new sources; version the library |
| Intent mapping too rigid | Content-adaptive overrides + allow Claude to hint at preferences |
| Performance of style resolution | Style library is small JSON (~50KB); loaded once, cached in memory |
| Proportional coordinates don't work for all content | Fallback to absolute positioning for complex elements (charts, tables) |
| Pipeline discovers too few useful patterns | 4 structural fallbacks guarantee plugin works; fallbacks use sensible defaults |
| Pipeline discovers unexpected/odd patterns | Confidence score + source_count filtering; low-confidence clusters excluded |
| Discovered patterns override a good fallback poorly | Manual curation step; can pin specific intents to fallbacks in config |
