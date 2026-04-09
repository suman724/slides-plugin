# Roadmap: Enterprise Enhancements

Proposed step-function improvements to make the `/slides` skill enterprise-grade. Each enhancement is designed to be implemented incrementally on top of the existing architecture.

---

## 1. Template Injection -- Use the Company's Own PPTX Template

**Priority**: Highest -- removes the #1 adoption blocker for enterprise teams.

**Problem**: Every enterprise has a mandated PowerPoint template with their logo, master slides, color scheme, and layout placeholders. No matter how good our generated slides look, if they don't use the company template, they won't pass review.

**Solution**: Accept a company `.pptx` template file. Preprocess it to extract layout-to-intent mappings, then populate the template's own placeholders instead of drawing shapes from scratch.

### How It Works

**Preprocessing** (one-time per template):

Run the existing `extract.py` on the company template, enhanced to also extract placeholder types:

```bash
python3 pipeline/extract.py --template acme_template.pptx --output acme_profile.json
```

The extractor reads each slide layout's placeholders (`TITLE`, `BODY`, `SUBTITLE`, `CENTER_TITLE`, `CHART`, `TABLE`, `PICTURE`) and auto-maps layouts to intents:

| Template Layout | Placeholders | Maps To |
|---|---|---|
| "Title Slide" | CENTER_TITLE + SUBTITLE | `open`, `close` |
| "Section Header" | TITLE | `divide` |
| "Title and Content" | TITLE + BODY | `explain`, `outline`, `measure`, `sequence`, `summarize`, `visualize`, `tabulate` |
| "Two Content" | TITLE + BODY + BODY | `compare`, `evaluate` |
| "Title Only" | TITLE | `emphasize` |
| "Blank" | (none) | fallback |

Output is a `template_profile.json` that the user can review and edit:

```json
{
  "template_file": "acme_template.pptx",
  "brand": {
    "colors": {"primary": "#003366", "accent": "#FF6600"},
    "fonts": {"heading": "Montserrat", "body": "Open Sans"}
  },
  "layouts": [
    {
      "index": 0,
      "name": "Title Slide",
      "placeholders": [
        {"idx": 0, "type": "CENTER_TITLE", "bounds_pct": {"left": 0.10, "top": 0.30, "width": 0.80, "height": 0.15}},
        {"idx": 1, "type": "SUBTITLE", "bounds_pct": {"left": 0.10, "top": 0.50, "width": 0.80, "height": 0.08}}
      ],
      "maps_to": ["open", "close"]
    }
  ]
}
```

**Rendering** (at generation time):

Two rendering modes, selected automatically:

```
Has template profile?
    |
   NO → current behavior (blank slides + add shapes from style library)
    |
  YES → use template's layout index + populate its placeholders
```

```python
if template_profile:
    layout_index = template_profile.get_layout_index(intent)
    slide = prs.slides.add_slide(prs.slide_layouts[layout_index])
    populate_placeholders(slide, content_mapping)
else:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    render_slide(slide, ...)
```

Populating placeholders preserves the template's exact formatting (fonts, colors, spacing all inherited from the master slide). This is why enterprise users prefer it -- the output is indistinguishable from a manually-built deck.

### How to Specify a Template

| Method | Example | When to Use |
|---|---|---|
| In JSON spec metadata | `"template": "./acme_template.pptx"` | Per-presentation |
| CLI flag | `--template acme.pptx` | Command line usage |
| Project config | `.slides-config.yaml` with `template: ./templates/acme.pptx` | Set once per project |
| Skill default | Drop PPTX in `~/.claude/skills/slides/templates/default.pptx` | Personal default |

Precedence: CLI flag > spec metadata > project config > skill default > none (shapes mode).

### What Already Exists vs. What's Missing

| Component | Status | Gap |
|---|---|---|
| Extractor (`extract.py`) | Exists | Needs to also extract placeholder types from slide layouts |
| Intent mapper | Exists | No change -- maps intents to layout patterns as-is |
| Style resolver | Exists | Template brand colors/fonts override style library |
| Overflow module | Exists | No change -- works on content regardless of rendering mode |
| Layout validator | Exists | No change -- validates shapes regardless of how they were created |
| Rendering path | **Missing** | New `populate_placeholders()` function alongside existing `render_slide()` |
| Generate entry point | Exists | Needs template mode switch (one `if/else`) |

### Implementation Estimate

- Extractor enhancement: ~50 lines (read placeholder types)
- Template profile output: ~30 lines (JSON serialization)
- Populate placeholders function: ~100 lines (new rendering path)
- Generate entry point change: ~15 lines (mode switch)
- Total: ~200 lines of new code

---

## 2. Data-to-Slides -- Read Excel/CSV and Auto-Generate Presentations

**Priority**: Highest -- creates a new capability, not just better output.

**Problem**: Enterprise users don't start with bullet points. They start with spreadsheets of quarterly numbers, CSV exports from BI tools, or financial models. Today Claude has to read the data in conversation and manually structure it into slides.

**Solution**: The skill reads data files directly, performs automated analysis (identify trends, outliers, composition, comparisons), and generates a complete data-driven presentation.

### How It Works

```
/slides from quarterly_data.xlsx
```

1. Claude reads the file using `pandas`
2. Analyzes the data:
   - Time series columns → `visualize` with line/column chart
   - Categorical data → `visualize` with column/bar chart
   - Composition/percentages → `visualize` with doughnut
   - Key metrics (single values) → `measure` with KPI cards
   - Comparison rows → `tabulate` with conditional highlighting
   - Text columns with few rows → `explain` with bullets
3. Generates the semantic JSON spec with appropriate intents and data
4. Normal rendering pipeline produces the PPTX

### Data Analysis Intelligence

| Data Pattern | Detected By | Intent |
|---|---|---|
| Column with dates/quarters + numeric values | dtype=datetime or regex Q[1-4] | `visualize` (line chart) |
| Column with categories + numeric values | dtype=object + dtype=float | `visualize` (column chart) |
| Row of percentages summing to ~100% | sum check | `visualize` (doughnut) |
| 3-5 rows with label + single number | shape check | `measure` (KPI cards) |
| Table with 4+ columns and 4+ rows | shape check | `tabulate` |
| Columns that increase/decrease monotonically | trend analysis | Chart annotation: "+X% growth" |
| Values with YoY pairs | column name matching | Highlight rules for variance |

### Implementation

- Add `pandas` to requirements
- New `data_analyzer.py` module (~200 lines) that reads Excel/CSV and outputs a semantic spec
- SKILL.md instructions for Claude to use the analyzer when data files are provided
- The rendering pipeline is unchanged

---

## 3. Visual Preview Loop -- See Slides in Conversation Before Exporting

**Priority**: High -- dramatically improves iteration speed.

**Problem**: Currently the user gets a PPTX file and has to open it in PowerPoint to see results. Each iteration cycle takes minutes.

**Solution**: After generating the PPTX, render slides as PNG thumbnails and display them inline in the Claude Code conversation. The user sees slides immediately and iterates in seconds.

### How It Works

```
/slides quarterly review
```

Claude generates the PPTX, then:

```bash
libreoffice --headless --convert-to pdf presentation.pptx
# or
libreoffice --headless --convert-to png presentation.pptx
```

The resulting images are displayed in the conversation. The user says "change slide 5 to a bar chart" and sees the updated preview immediately.

### Implementation Options

| Method | Pros | Cons |
|---|---|---|
| LibreOffice headless | High fidelity, exact PPTX rendering | Requires LibreOffice installed |
| `pdf2image` (poppler) | Good fidelity after PDF conversion | Two-step: PPTX → PDF → PNG |
| `python-pptx` + `Pillow` | No external deps | Limited rendering (no charts/effects) |
| macOS `qlmanage` | Native, fast | macOS only |

Recommended: LibreOffice headless. Most enterprise environments have it, and it renders PPTX faithfully.

### Implementation

- New `preview.py` module (~50 lines) that converts PPTX to thumbnails
- SKILL.md instructions to generate and display previews after rendering
- No changes to rendering pipeline

---

## 4. Speaker Notes + Narrative Intelligence

**Priority**: High -- mostly LLM work, little code needed.

**Problem**: Enterprise presentations are performed, not just read. Slides need speaker notes with talking points, data callouts, and transitions. Currently slides are isolated with no narrative analysis.

**Solution**: Two capabilities:

### Speaker Notes

For each slide, generate contextual speaking notes:
- Key message (1 sentence)
- Supporting data points to reference
- Transition phrase to next slide
- Potential audience questions

Add to the semantic spec:

```json
{
  "intent": "explain",
  "title": "Key Market Trends",
  "points": [...],
  "speaker_notes": "Key message: TAM growth validates our market expansion strategy. Highlight the 65% enterprise concentration -- this supports our ABM investment. Transition: these trends set up the financial performance we'll see next."
}
```

python-pptx supports notes via `slide.notes_slide.notes_text_frame`. Implementation is ~10 lines in the renderer.

### Narrative Analysis

After generating the full deck spec, Claude analyzes it for:
- **Flow gaps**: "You have data but no conclusion slide"
- **Ordering issues**: "The comparison should come before the recommendation"
- **Missing transitions**: "Add a section divider between finance and strategy"
- **Balance**: "7 slides on analysis but only 1 on recommendations"

This is pure SKILL.md instruction -- Claude does the analysis using its LLM capabilities, no code changes needed.

### Implementation

- Add `speaker_notes` field to semantic content model
- ~10 lines in `shape_renderer.py` to populate notes
- SKILL.md instructions for narrative analysis and notes generation
- Update reference docs

---

## 5. Brand Kit System -- Corporate Identity Beyond Colors

**Priority**: Medium-High -- makes the skill sticky for teams.

**Problem**: Enterprise brand guidelines go beyond colors: logo placement, approved fonts, heading capitalization, chart style rules, legal disclaimers, copyright footers, minimum margins.

**Solution**: A `brand_kit.yaml` configuration that encodes all brand rules. The skill loads it and enforces every rule automatically.

### Brand Kit Format

```yaml
# brand_kit.yaml
company: "Acme Corp"

identity:
  logo_path: "./assets/acme_logo.png"
  logo_position: "top_right"
  logo_max_height_inches: 0.5

colors:
  primary: "#003366"
  secondary: "#006699"
  accent: "#FF6600"
  positive: "#228B22"
  negative: "#CC0000"

fonts:
  heading: "Montserrat"
  body: "Open Sans"
  monospace: "Source Code Pro"

rules:
  title_case: "sentence"           # "sentence", "title", "upper"
  max_bullets_per_slide: 5         # stricter than default 8
  max_slides: 15                   # company standard
  chart_style: "flat"              # "flat", "shadow", "3d" (most brands ban 3d)
  gridlines: false
  data_labels: true

footer:
  left: "© 2026 Acme Corp"
  center: "Confidential"
  right: "auto_page_number"        # "{page} / {total}"

compliance:
  disclaimer: "This document is proprietary and confidential."
  disclaimer_slide: "last"         # "first", "last", "both"
```

### How It Integrates

Brand kit is the highest-priority style source:

```
brand_kit.yaml  >  template_profile.json  >  style_library.json  >  defaults
```

The style resolver checks for a brand kit first, then falls through to template profile, then style library.

### Implementation

- New `brand_resolver.py` (~100 lines) that reads YAML and produces a `ResolvedStyle` override
- Logo insertion in the shape renderer (~20 lines)
- Footer override in the footer renderer (~10 lines)
- Title case enforcement in the overflow module (~15 lines)
- SKILL.md instructions for brand kit usage

---

## 6. Presentation Remix -- Transform Existing Decks

**Priority**: Medium-High -- covers the 80% of presentation work that involves existing content.

**Problem**: The skill only creates new presentations. But most enterprise work involves updating, reformatting, or combining existing decks.

**Solution**: Read an existing PPTX, extract content into the semantic spec format (reverse pipeline), then regenerate with new styling, updated data, or combined with other sources.

### Use Cases

```
/slides remix old_deck.pptx --template new_template.pptx
/slides update last_quarter.pptx --set revenue=185B growth=18%
/slides combine team_a.pptx team_b.pptx --into executive_summary.pptx
```

### How It Works

**Reverse extraction** (PPTX → semantic spec):

1. Read each slide's shapes
2. Classify content: bullets → `explain`, charts → `visualize`, tables → `tabulate`, KPI-like layout → `measure`
3. Extract text, data, chart values
4. Build a semantic JSON spec
5. User can edit the spec, then regenerate with a different template/style

### Implementation

- New `reverse_extract.py` (~200 lines) that reads PPTX and outputs semantic spec
- Content classification heuristics (reuse extraction pipeline logic)
- SKILL.md instructions for remix workflows
- No changes to rendering pipeline

---

## 7. Multi-Deck Intelligence -- Learn from Previous Presentations

**Priority**: Medium -- long-term stickiness for teams.

**Problem**: Enterprise teams create dozens of similar presentations (monthly reports, quarterly reviews, client updates). Each is built from scratch with no learning across presentations.

**Solution**: The skill maintains a lightweight history of generated specs. When generating a new presentation on a similar topic, it references previous structure.

### How It Works

```
/slides April monthly report
```

1. Skill searches `~/.claude/slides-history/` for specs with similar titles/topics
2. Finds `march_monthly_report.spec.json`
3. Offers: "Found March's monthly report structure. Use the same format with updated data?"
4. If yes: reuses the slide structure, user provides new data
5. Saves the new spec to history for next month

### History Storage

```
~/.claude/slides-history/
├── 2026-03-monthly-report.spec.json
├── 2026-04-board-deck.spec.json
├── 2026-04-client-update-acme.spec.json
└── index.json   # topic, date, file path for search
```

### Implementation

- History save: ~20 lines in `generate_pptx.py` (save spec after generation)
- History search: ~50 lines (fuzzy title matching)
- SKILL.md instructions to check history and offer reuse
- No changes to rendering pipeline

---

## Implementation Priority

| # | Enhancement | Effort | Impact | Dependencies |
|---|---|---|---|---|
| 1 | Template Injection | ~200 lines | Highest | None |
| 2 | Data-to-Slides | ~200 lines | Highest | pandas |
| 3 | Visual Preview | ~50 lines | High | LibreOffice |
| 4 | Speaker Notes + Narrative | ~30 lines | High | None |
| 5 | Brand Kit | ~150 lines | Medium-High | Enhancement 1 |
| 6 | Presentation Remix | ~200 lines | Medium-High | None |
| 7 | Multi-Deck Intelligence | ~70 lines | Medium | None |

Enhancements 1-4 can be built independently. Enhancement 5 builds on 1 (brand kit + template together is the enterprise sweet spot). Enhancements 6-7 are standalone.
