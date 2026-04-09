# Slide Layout Types

Quick reference for when to use each slide type.

## Structural Slides

### `title`
**When to use:** Always the first slide. Cover/opening slide.
**Visual:** Gradient background (primary -> secondary), large title, subtitle, accent bar, footer band.

### `closing`
**When to use:** Always the last slide.
**Visual:** Same gradient as title slide, centered "Thank You" text, contact info.

### `agenda`
**When to use:** Second slide for decks with 3+ sections. Shows what the presentation covers.
**Visual:** Numbered items with accent-colored circles, main text + subtext.

### `section_divider`
**When to use:** Before each major section in longer decks (8+ slides).
**Visual:** Left band with primary color + large section number, title on right with accent bar.

## Content Slides

### `content`
**When to use:** Standard information delivery. The workhorse slide.
**Visual:** Title + bullet list. Supports 2 indent levels (bullets + sub-bullets).
**Tips:** Keep to 5-7 bullets max. Use level 1 for supporting details.

### `two_column`
**When to use:** Comparing two related topics, showing "before/after", or splitting related content.
**Visual:** Title + two equal columns, each with heading, separator line, and bullets.

### `three_column`
**When to use:** Comparing three items or categorizing information.
**Visual:** Title + three equal columns with headings and bullets.

## Data Slides

### `chart`
**When to use:** When you have quantitative data to visualize.
**Supported types:** column_clustered, column_stacked, bar_clustered, bar_stacked, line, line_markers, pie, area, area_stacked, doughnut.
**Visual:** Title + chart + optional annotation text below.
**Tips:** Choose chart type based on data: trends = line, comparison = column, composition = pie.

### `table`
**When to use:** Detailed data that needs exact values visible (financials, feature comparisons).
**Visual:** Title + formatted table with styled header row, alternating row shading, conditional highlighting.

### `key_metrics`
**When to use:** When you have 3-4 KPIs to showcase prominently.
**Visual:** Title + metric cards in a row. Each card shows large value, label, and delta with direction arrow.
**Tips:** Great for executive dashboards and status updates.

### `big_number`
**When to use:** When one statistic deserves its own slide for impact.
**Visual:** Title + one huge number (80pt) in accent color + label + context text.

## Analysis Slides

### `comparison`
**When to use:** Evaluating options, pros/cons analysis.
**Visual:** Title + two side-by-side cards with headings, advantage lists (green checks), and challenge lists (red crosses).

### `timeline`
**When to use:** Roadmaps, project plans, historical progressions.
**Visual:** Title + horizontal line with circular milestone markers. Date above, label and detail below each marker.

### `takeaway`
**When to use:** Summarizing key findings before closing. Usually the second-to-last slide.
**Visual:** Title + numbered takeaway points + optional call-to-action box in accent color.

## Special Slides

### `quote`
**When to use:** Highlighting an important quote from a leader, customer, or thought leader.
**Visual:** Large opening quote mark, italic quote text, attribution line.

### `image_with_text`
**When to use:** When visual evidence supports the narrative (screenshots, diagrams, photos).
**Visual:** Left half = image (or placeholder), right half = text/bullets.
**Note:** Provide `image_path` for real images; omit for a gray placeholder box.
