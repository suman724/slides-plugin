# Intent Reference

Quick reference for when to use each semantic intent.

## Structural Intents

| Intent | When to Use | Example |
|---|---|---|
| `open` | Always first slide | Cover with title and subtitle |
| `close` | Always last slide | Thank you with contact info |
| `outline` | Second slide for 3+ sections | Numbered agenda items |
| `divide` | Before each major section | Section number + title |

## Content Intents

| Intent | When to Use | Example |
|---|---|---|
| `explain` | Standard information delivery | Bullet points about market trends |
| `compare` | Two things side by side | Revenue vs. Plan, Before vs. After |
| `categorize` | Three or more parallel categories | Phase 1 / Phase 2 / Phase 3 |

## Data Intents

| Intent | When to Use | Example |
|---|---|---|
| `measure` | 3-4 key performance indicators | ARR, NRR, Churn, CAC Payback |
| `visualize` | Quantitative data to chart | Revenue by quarter, growth trends |
| `tabulate` | Exact values need to be visible | P&L summary, feature comparison matrix |

## Analysis Intents

| Intent | When to Use | Example |
|---|---|---|
| `evaluate` | Weighing options with pros/cons | Build vs. Buy, Option A vs. B |
| `sequence` | Roadmap or timeline | Implementation milestones |
| `summarize` | Key findings before closing | 3 takeaways + call to action |

## Special Intents

| Intent | When to Use | Example |
|---|---|---|
| `emphasize` | One stat or quote deserves its own slide | "$4.2B TAM" or an executive quote |
| `illustrate` | Visual evidence supports the narrative | Screenshot + bullet points |

## Intent Selection Guide

| Content Type | Recommended Intent |
|---|---|
| Opening | `open` |
| Table of contents | `outline` |
| Section break | `divide` |
| Bullet points | `explain` |
| Side-by-side info | `compare` |
| Three+ categories | `categorize` |
| Trends over time | `visualize` (line chart) |
| Category comparison | `visualize` (column chart) |
| Composition/share | `visualize` (pie chart) |
| Detailed data | `tabulate` |
| 3-4 KPIs | `measure` |
| Options evaluation | `evaluate` |
| Project plan | `sequence` |
| Summary | `summarize` |
| Impactful stat | `emphasize` (number) |
| Notable quote | `emphasize` (quote) |
| Visual + text | `illustrate` |
| Ending | `close` |

## Content-Adaptive Behavior

The engine automatically adjusts based on content:
- `compare` with 3+ sides -> upgrades to `categorize` (3-column layout)
- `explain` with 1 short point -> adapts to `emphasize`
- `measure` with 5-6 metrics -> uses a 2-row grid layout
- `measure` with 7+ metrics -> splits across multiple slides of 4
- `evaluate` with 3 options -> uses 3-column layout
- `evaluate` with 4+ options -> splits into paired slides of 2
- `sequence` with 7-10 milestones -> compresses label sizes
- `sequence` with 11+ milestones -> splits into 2 timeline slides
- `tabulate` with 12+ rows -> splits into multiple table slides
- `visualize` with 12+ chart categories -> switches column to bar chart or truncates

## Deck Structure Patterns

### Executive Review (10-15 slides)
`open` -> `outline` -> `divide` + `measure` + `visualize` -> `divide` + `explain` + `compare` -> `divide` + `sequence` + `summarize` -> `close`

### Project Update (8-12 slides)
`open` -> `outline` -> `measure` -> `explain` -> `compare` (risks) -> `summarize` -> `close`

### Strategy Presentation (12-18 slides)
`open` -> `outline` -> `emphasize` (market size) -> `explain` + `visualize` -> `evaluate` (options) -> `summarize` -> `sequence` (roadmap) -> `close`

### Product Launch (8-12 slides)
`open` -> `emphasize` (problem) -> `explain` (solution) -> `categorize` (features) -> `visualize` (market) -> `sequence` (go-to-market) -> `summarize` -> `close`

### Research Report (10-14 slides)
`open` -> `outline` -> `explain` (methodology) -> `visualize` + `tabulate` (findings) -> `emphasize` (key insight) -> `illustrate` (evidence) -> `summarize` (recommendations) -> `close`
