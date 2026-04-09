# JSON Slide Specification Schema

The JSON specification is the contract between Claude (content generator) and the Python renderer. Claude generates this JSON; `generate_pptx.py` consumes it.

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
| `date` | string | no | Date string (appears on title slide) |
| `confidentiality` | string | no | E.g., "Confidential" (appears in footer) |
| `theme` | string | no | Theme name: `corporate_blue`, `modern_dark`, `minimal`. Default: `corporate_blue` |
| `output_path` | string | no | Output file path. Default: `./presentation.pptx` |

## Slide Types

Each slide in the `slides` array has a `type` field that determines its layout. Below are all supported types with their fields.

### `title`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"title"` | yes | |
| `title` | string | yes | Main title text |
| `subtitle` | string | no | Subtitle text |
| `date` | string | no | Date (overrides metadata date) |
| `confidentiality` | string | no | Footer confidentiality text |
| `footer_right` | string | no | Right-side footer text |

### `closing`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"closing"` | yes | |
| `title` | string | yes | Usually "Thank You" |
| `subtitle` | string | no | E.g., "Questions & Discussion" |
| `contact` | string | no | Contact email or info |

### `agenda`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"agenda"` | yes | |
| `title` | string | yes | Usually "Agenda" |
| `items` | array | yes | List of agenda items |

Each agenda item:

| Field | Type | Required | Description |
|---|---|---|---|
| `number` | int | no | Item number (auto-assigned if omitted) |
| `text` | string | yes | Main text |
| `subtext` | string | no | Secondary description |

### `section_divider`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"section_divider"` | yes | |
| `section_number` | int | no | Section number displayed large |
| `title` | string | yes | Section title |
| `subtitle` | string | no | Section subtitle |

### `content`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"content"` | yes | |
| `title` | string | yes | Slide title |
| `body` | array | yes | List of body items |

Body item format:

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"bullet"` | yes | Item type |
| `text` | string | yes | Text content |
| `level` | int | no | Indent level: 0 (default) or 1 (sub-bullet) |

### `two_column`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"two_column"` | yes | |
| `title` | string | yes | Slide title |
| `left` | object | yes | Left column content |
| `right` | object | yes | Right column content |

Column object:

| Field | Type | Required | Description |
|---|---|---|---|
| `heading` | string | no | Column heading |
| `body` | array | yes | List of body items (same format as `content`) |

### `three_column`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"three_column"` | yes | |
| `title` | string | yes | Slide title |
| `columns` | array | yes | List of 3 column objects (same as two_column) |

### `chart`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"chart"` | yes | |
| `title` | string | yes | Slide title |
| `chart_type` | string | yes | Chart type (see below) |
| `categories` | array | yes | Category labels (x-axis) |
| `series` | array | yes | Data series |
| `annotation` | string | no | Text below chart |

Supported chart types: `column_clustered`, `column_stacked`, `bar_clustered`, `bar_stacked`, `line`, `line_markers`, `pie`, `area`, `area_stacked`, `doughnut`

Series format: `{"name": "Series Name", "values": [1, 2, 3]}`

### `table`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"table"` | yes | |
| `title` | string | yes | Slide title |
| `columns` | array | yes | Column header strings |
| `rows` | array | yes | List of row arrays (each row = list of cell strings) |
| `highlight_rules` | array | no | Conditional formatting rules |

Highlight rule format:

| Field | Type | Description |
|---|---|---|
| `column` | int | Column index (0-based) |
| `condition` | string | `"negative"` or `"positive"` |
| `color` | string | `"red"`, `"green"`, `"blue"`, or `"gray"` |

### `key_metrics`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"key_metrics"` | yes | |
| `title` | string | yes | Slide title |
| `metrics` | array | yes | List of 3-4 metric objects |

Metric format:

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | yes | Metric name (e.g., "ARR") |
| `value` | string | yes | Displayed value (e.g., "$568M") |
| `delta` | string | no | Change indicator (e.g., "+18%") |
| `direction` | string | no | `"up"` or `"down"` (determines color) |

### `comparison`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"comparison"` | yes | |
| `title` | string | yes | Slide title |
| `left` | object | yes | Left option |
| `right` | object | yes | Right option |

Option object:

| Field | Type | Required | Description |
|---|---|---|---|
| `heading` | string | yes | Option name |
| `pros` | array | yes | List of advantage strings |
| `cons` | array | yes | List of challenge strings |

### `timeline`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"timeline"` | yes | |
| `title` | string | yes | Slide title |
| `milestones` | array | yes | List of milestone objects |

Milestone format:

| Field | Type | Required | Description |
|---|---|---|---|
| `date` | string | yes | Date label (e.g., "Q4 2026") |
| `label` | string | yes | Milestone name |
| `detail` | string | no | Additional detail text |

### `takeaway`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"takeaway"` | yes | |
| `title` | string | yes | Usually "Key Takeaways" |
| `points` | array | yes | List of takeaway strings |
| `call_to_action` | string | no | CTA text (displayed in accent-colored box) |

### `quote`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"quote"` | yes | |
| `title` | string | no | Slide title (can be empty) |
| `quote` | string | yes | Quote text |
| `attribution` | string | no | Who said it |

### `image_with_text`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"image_with_text"` | yes | |
| `title` | string | yes | Slide title |
| `image_path` | string | no | Path to image file (shows placeholder if omitted) |
| `body` | array | no | Body items (same format as `content`) |
| `text` | string | no | Plain text alternative to body |

### `big_number`

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `"big_number"` | yes | |
| `title` | string | no | Slide title |
| `value` | string | yes | The big number (e.g., "$4.2B") |
| `label` | string | no | What the number represents |
| `context` | string | no | Additional context text |
