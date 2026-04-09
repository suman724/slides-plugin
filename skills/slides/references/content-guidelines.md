# Content Guidelines

## Augmentation Levels

### Level 1: Minimal Input
The user provides just a topic (e.g., `/slides quarterly review`).

- Generate a complete 10-12 slide deck with plausible structure
- Follow the standard deck pattern: `open` -> `outline` -> sections with `divide` -> `summarize` -> `close`
- Use realistic but clearly synthetic data where needed
- Structure: 3-4 sections with 2-3 content slides each

### Level 2: Structured Input
The user provides topic + some data (e.g., `/slides quarterly review: revenue $142M, growth 18%`).

- Use provided data points as anchors
- Generate supporting slides around the data
- Fill in context and analysis
- 8-12 slides

### Level 3: Detailed Input
The user provides a full outline or pastes a document.

- Structure the content into slides faithfully
- Focus on intent selection and content organization
- Add `open`/`close` if missing
- Generate as many slides as content warrants

## Content Quality Rules

1. **Every slide needs a clear title** -- descriptive, not generic ("Revenue Growth Drivers" not "Slide 5")
2. **5-7 bullets max per slide** -- if you have more, split across slides
3. **Be specific** -- use numbers, dates, and names instead of vague statements
4. **Parallel structure** -- all bullets at the same level should follow the same grammatical pattern
5. **Action-oriented** -- prefer "Revenue grew 18% to $142M" over "Revenue was $142M"
6. **No walls of text** -- slides are visual aids, not documents

## Intent Selection by Content Type

| Content | Intent | Why |
|---|---|---|
| Opening | `open` | Structural necessity |
| Agenda / TOC | `outline` | Numbered items with optional detail |
| Section break | `divide` | Navigation between major sections |
| Bullet points | `explain` | The workhorse for narrative content |
| Two-sided comparison | `compare` | Side-by-side with headings |
| Three+ categories | `categorize` | Multi-column comparison |
| Trends over time | `visualize` (line) | Time-series data |
| Category comparison | `visualize` (column) | Discrete category data |
| Composition/share | `visualize` (pie) | Part-of-whole data |
| Exact values table | `tabulate` | When readers need specific numbers |
| 3-4 headline metrics | `measure` | KPI dashboard cards |
| Options with pros/cons | `evaluate` | Decision support |
| Project timeline | `sequence` | Milestones on a roadmap |
| Single standout stat | `emphasize` (number) | Maximum impact for one number |
| Notable quote | `emphasize` (quote) | Executive or thought leader quote |
| Image + commentary | `illustrate` | Visual evidence + text |
| Key findings | `summarize` | Numbered takeaways + call to action |
| Ending | `close` | Thank you + contact |

## Deck Structure Patterns

### Executive Review (10-15 slides)
`open` -> `outline` -> `divide` + `measure` + `visualize` (performance) -> `divide` + `explain` + `compare` (analysis) -> `divide` + `sequence` + `summarize` (outlook) -> `close`

### Project Update (8-12 slides)
`open` -> `outline` -> `measure` (status) -> `explain` (progress) -> `compare` (risks vs. mitigations) -> `summarize` (next steps) -> `close`

### Strategy Presentation (12-18 slides)
`open` -> `outline` -> `emphasize` (market size) -> `explain` + `visualize` (current state) -> `evaluate` (strategic options) -> `summarize` (recommendation) -> `sequence` (roadmap) -> `close`

### Product Launch (8-12 slides)
`open` -> `emphasize` (problem statement) -> `explain` (solution) -> `categorize` (key features) -> `visualize` (market opportunity) -> `sequence` (go-to-market) -> `summarize` (ask) -> `close`

### Research Report (10-14 slides)
`open` -> `outline` -> `explain` (methodology) -> `visualize` + `tabulate` (findings) -> `emphasize` (key insight) -> `illustrate` (evidence) -> `summarize` (recommendations) -> `close`

## Overflow Handling

The engine handles content overflow automatically, but better content = fewer adjustments:
- **Bullets > 8**: Engine reduces spacing/font first, then splits across slides. Prefer splitting in the spec.
- **Titles > 60 chars**: Engine reduces font size first (down to 20pt), truncates as last resort. Keep titles concise.
- **Metrics > 4**: 5-6 use a 2-row grid. 7+ split across slides. Group related KPIs together.
- **Table rows > 12**: Engine splits, repeating headers. Consider summarizing data instead.
- **Table columns > 7**: Engine reduces cell font to 8pt. Consider transposing if row count is low.
- **Timeline > 6**: Engine compresses labels. 11+ splits into 2 slides. Show only key milestones.
- **Chart > 12 categories**: Engine switches column to bar chart or truncates. Aggregate where possible.
- **Evaluate > 3 options**: 3 uses 3-column, 4+ splits into paired slides. Keep to 2-3 options per slide.
