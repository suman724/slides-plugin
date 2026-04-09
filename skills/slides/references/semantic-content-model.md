# Semantic Content Model

The JSON specification uses semantic intents -- describe WHAT the content is, not HOW to lay it out. The rendering engine determines layout automatically.

## Top-Level Structure

```json
{
  "metadata": { ... },
  "slides": [ ... ]
}
```

## Metadata

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | yes | Presentation title |
| `subtitle` | string | no | Presentation subtitle |
| `author` | string | no | Author name |
| `company` | string | no | Company name (appears in footer) |
| `date` | string | no | Date string (appears on cover) |
| `confidentiality` | string | no | E.g., "Confidential" (appears in footer) |
| `style` | object | no | Style preferences (see below) |

### Style Object

| Field | Type | Description |
|---|---|---|
| `palette` | string | Exact palette ID from style library |
| `mood` | string | `"professional"`, `"bold"`, `"warm"`, `"minimal"` |
| `typography` | string | Exact typography pattern ID |
| `font` | string | Font family name to match |

If omitted, defaults to the first palette in the style library.

**Note:** Currently most palettes in the library have mood `"professional"`. If you specify `"bold"`, `"warm"`, or `"minimal"` and no palette matches, the engine falls back to the default. This will improve as more diverse source PPTX files are added to the pipeline.

## Slide Intents

Each slide has an `intent` field and intent-specific content fields.

---

### `open`

Opening/cover slide.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"open"` | yes | |
| `title` | string | yes | Main title |
| `subtitle` | string | no | Subtitle text |
| `date` | string | no | Date (overrides metadata date on cover) |

```json
{"intent": "open", "title": "Q3 2026 Strategic Review", "subtitle": "Board of Directors"}
```

---

### `close`

Closing/thank-you slide.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"close"` | yes | |
| `title` | string | yes | Usually "Thank You" |
| `subtitle` | string | no | E.g., "Questions & Discussion" |
| `contact` | string | no | Contact email or info |

```json
{"intent": "close", "title": "Thank You", "subtitle": "Questions?", "contact": "team@acme.com"}
```

---

### `outline`

Table of contents / agenda.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"outline"` | yes | |
| `title` | string | yes | Usually "Agenda" |
| `items` | array | yes | List of agenda items |

Each item: `{"text": "Topic Name", "detail": "Optional description"}`

```json
{
  "intent": "outline",
  "title": "Agenda",
  "items": [
    {"text": "Market Overview", "detail": "Industry trends"},
    {"text": "Financial Performance", "detail": "Revenue and margins"}
  ]
}
```

---

### `divide`

Section break / divider.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"divide"` | yes | |
| `title` | string | yes | Section title |
| `subtitle` | string | no | Section description |
| `section_number` | int | no | Displayed as large formatted number |

```json
{"intent": "divide", "title": "Market Overview", "subtitle": "Industry trends", "section_number": 1}
```

---

### `explain`

Standard bullet points with optional sub-bullets.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"explain"` | yes | |
| `title` | string | yes | Slide title |
| `points` | array | yes | List of point objects |

Each point: `{"text": "Main point", "subpoints": ["Detail 1", "Detail 2"]}`

The `subpoints` field is optional. Points can also be plain strings.

```json
{
  "intent": "explain",
  "title": "Key Market Trends",
  "points": [
    {"text": "TAM grew 12% YoY to $4.2B", "subpoints": ["Enterprise: 65% of growth"]},
    {"text": "Competitor X launched adjacent product"},
    {"text": "Regulatory changes expected in H2"}
  ]
}
```

---

### `compare`

Side-by-side comparison of 2 items.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"compare"` | yes | |
| `title` | string | yes | Slide title |
| `sides` | array | yes | 2 side objects |

Each side: `{"heading": "Label", "points": ["Point 1", "Point 2"]}`

If you provide 3+ sides, the engine automatically upgrades to a `categorize` layout.

```json
{
  "intent": "compare",
  "title": "Revenue vs. Plan",
  "sides": [
    {"heading": "Performance", "points": ["Revenue: $142M", "Margin: 72%"]},
    {"heading": "Commentary", "points": ["Pipeline strong", "Churn elevated"]}
  ]
}
```

---

### `categorize`

Three or more parallel categories.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"categorize"` | yes | |
| `title` | string | yes | Slide title |
| `sides` | array | yes | 3+ side objects (same format as `compare`) |

```json
{
  "intent": "categorize",
  "title": "Implementation Phases",
  "sides": [
    {"heading": "Phase 1", "points": ["Foundation", "Core features"]},
    {"heading": "Phase 2", "points": ["Integration", "Testing"]},
    {"heading": "Phase 3", "points": ["Optimization", "Launch"]}
  ]
}
```

---

### `measure`

KPI / metric dashboard.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"measure"` | yes | |
| `title` | string | yes | Slide title |
| `metrics` | array | yes | 3-4 metric objects (5+ triggers overflow handling) |

Each metric:

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | yes | Metric name (e.g., "ARR") |
| `value` | string | yes | Displayed value (e.g., "$568M") |
| `change` | string | no | Change indicator (e.g., "+18%") |
| `trend` | string | no | `"up"` or `"down"` -- determines arrow color (green/red) |

```json
{
  "intent": "measure",
  "title": "Key Performance Indicators",
  "metrics": [
    {"label": "ARR", "value": "$568M", "change": "+18%", "trend": "up"},
    {"label": "Churn", "value": "4.2%", "change": "+0.8pp", "trend": "down"}
  ]
}
```

---

### `visualize`

Chart / data visualization.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"visualize"` | yes | |
| `title` | string | yes | Slide title |
| `chart` | object | yes | Chart specification |
| `note` | string | no | Annotation text below chart |

Chart object:

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | yes | Chart type (see below) |
| `categories` | array | yes | Category labels (x-axis) |
| `series` | array | yes | Data series |

Each series: `{"name": "Series Name", "values": [1, 2, 3]}`

Chart types: `column_clustered`, `column_stacked`, `bar_clustered`, `bar_stacked`, `line`, `line_markers`, `pie`, `area`, `area_stacked`, `doughnut`

```json
{
  "intent": "visualize",
  "title": "Revenue by Quarter",
  "chart": {
    "type": "column_clustered",
    "categories": ["Q1", "Q2", "Q3"],
    "series": [{"name": "Revenue ($M)", "values": [128, 135, 142]}]
  },
  "note": "Q3 within 2% of target"
}
```

---

### `tabulate`

Data table with optional conditional highlighting.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"tabulate"` | yes | |
| `title` | string | yes | Slide title |
| `columns` | array of strings | yes | Column header labels |
| `rows` | array of arrays | yes | Row data (each row = list of cell strings) |
| `highlight_rules` | array | no | Conditional formatting rules |

Highlight rule:

| Field | Type | Description |
|---|---|---|
| `column` | int | Column index (0-based) |
| `condition` | string | `"negative"` (starts with `-` or `(`) or `"positive"` (starts with `+` or digit) |
| `color` | string | `"red"`, `"green"`, `"blue"`, or `"gray"` |

```json
{
  "intent": "tabulate",
  "title": "P&L Summary ($M)",
  "columns": ["Metric", "Actual", "Plan", "Variance"],
  "rows": [["Revenue", "142", "145", "-2%"], ["EBITDA", "38", "40", "-5%"]],
  "highlight_rules": [{"column": 3, "condition": "negative", "color": "red"}]
}
```

---

### `evaluate`

Pros/cons analysis with advantages and challenges.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"evaluate"` | yes | |
| `title` | string | yes | Slide title |
| `options` | array | yes | 2 option objects (3+ triggers overflow: 3 uses 3-column, 4+ splits into paired slides) |

Each option:

| Field | Type | Required | Description |
|---|---|---|---|
| `heading` | string | yes | Option name |
| `advantages` | array | yes | List of advantage strings |
| `challenges` | array | yes | List of challenge strings |

```json
{
  "intent": "evaluate",
  "title": "Strategic Options",
  "options": [
    {"heading": "Organic Growth", "advantages": ["Lower risk"], "challenges": ["Slower"]},
    {"heading": "Acquisition", "advantages": ["Immediate share"], "challenges": ["$200M cost"]}
  ]
}
```

---

### `sequence`

Timeline / roadmap with milestones.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"sequence"` | yes | |
| `title` | string | yes | Slide title |
| `steps` | array | yes | List of milestone objects |

Each step:

| Field | Type | Required | Description |
|---|---|---|---|
| `when` | string | yes | Date/time label (e.g., "Q4 2026") |
| `what` | string | yes | Milestone name |
| `detail` | string | no | Additional description |

```json
{
  "intent": "sequence",
  "title": "Implementation Roadmap",
  "steps": [
    {"when": "Q4 2026", "what": "Board Approval", "detail": "Final decision"},
    {"when": "Q1 2027", "what": "Execution Begins", "detail": "Team formation"}
  ]
}
```

---

### `emphasize`

Big number or notable quote -- one impactful element per slide.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"emphasize"` | yes | |
| `title` | string | no | Slide title (can be empty for quotes) |
| `emphasis` | object | yes | The emphasis content |

**Number emphasis:**
```json
{
  "intent": "emphasize",
  "title": "Market Opportunity",
  "emphasis": {"type": "number", "value": "$4.2B", "label": "Total Addressable Market", "context": "Growing at 12% annually"}
}
```

**Quote emphasis:**
```json
{
  "intent": "emphasize",
  "emphasis": {"type": "quote", "text": "The best way to predict the future is to create it.", "attribution": "Peter Drucker"}
}
```

---

### `illustrate`

Image (or placeholder) with accompanying text.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"illustrate"` | yes | |
| `title` | string | yes | Slide title |
| `image_path` | string | no | Path to image file. Shows placeholder if omitted. |
| `points` | array | no | Bullet points (same format as `explain`) |
| `text` | string | no | Plain text alternative to points |

Provide either `points` or `text` for the right side, not both.

```json
{
  "intent": "illustrate",
  "title": "Product Dashboard",
  "points": [
    {"text": "Real-time visibility into key metrics"},
    {"text": "Customizable widgets per team"},
    {"text": "Mobile-responsive design"}
  ]
}
```

---

### `summarize`

Key takeaways with optional call-to-action.

| Field | Type | Required | Description |
|---|---|---|---|
| `intent` | `"summarize"` | yes | |
| `title` | string | yes | Usually "Key Takeaways" |
| `takeaways` | array of strings | yes | Numbered takeaway points |
| `action` | string | no | Call-to-action text (displayed in accent-colored box) |

```json
{
  "intent": "summarize",
  "title": "Key Takeaways",
  "takeaways": [
    "Q3 performance strong; revenue within 2% of plan",
    "Enterprise pipeline robust; SMB churn needs action"
  ],
  "action": "Approve Strategic Evaluation Committee"
}
```
