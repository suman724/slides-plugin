---
name: slides
description: Generate enterprise-quality PPTX presentations. Use when the user asks to create a presentation, make slides, generate a PowerPoint, build a deck, create a pitch deck, or mentions making professional presentations, board decks, strategy presentations, or slide generation.
argument-hint: <topic or detailed context>
allowed-tools: Bash Read Write
---

# Enterprise PPTX Presentation Generator

Generate professional, enterprise-quality PowerPoint presentations from user-provided context. Output is a `.pptx` file created programmatically using Python and python-pptx, with visual styles derived from a library of real enterprise presentation designs.

## Workflow

Follow these steps exactly:

### Step 1: Gather Context

Collect all available information before generating the specification:

- **`$ARGUMENTS`**: The topic, title, or context provided with the `/slides` command
- **Conversation history**: Any documents, data, files, or discussion from the current conversation that are relevant to the presentation
- **User preferences**: Look for style cues (`--mood professional`, `--output path.pptx`), structural hints ("compare X and Y", "timeline for..."), or explicit data points (metrics, KPIs, dates)

If the user provided files or data earlier in the conversation, incorporate that content into the slides. Do not ask for information that has already been provided.

### Step 2: Determine Content Augmentation Level

- **Minimal input** (just a topic like "quarterly review"): Generate a complete 10-12 slide deck with plausible structure and content. Use the conversation context to fill in specifics where possible.
- **Structured input** (topic + some data points): Use provided data as anchors, fill surrounding context. Generate 8-12 slides.
- **Detailed input** (full outline or pasted document): Structure and format faithfully. Add open/close slides if missing.

### Step 3: Generate Semantic JSON Specification

Create a JSON specification using **semantic intents** -- describe WHAT the content is, not HOW to lay it out. The rendering engine determines visual layout automatically.

See [references/semantic-content-model.md](references/semantic-content-model.md) for the full schema and [references/intent-reference.md](references/intent-reference.md) for all 15 intents with examples.

**Top-level structure:**

```json
{
  "metadata": {
    "title": "Presentation Title",
    "subtitle": "Optional subtitle",
    "author": "Author Name",
    "company": "Company Name",
    "date": "April 2026",
    "confidentiality": "Confidential",
    "style": {
      "mood": "professional"
    }
  },
  "slides": [
    {"intent": "open", "title": "...", "subtitle": "..."},
    {"intent": "explain", "title": "...", "points": [...]},
    {"intent": "close", "title": "Thank You"}
  ]
}
```

**Available intents:**
- `open` -- Cover/opening slide
- `close` -- Thank you/ending slide
- `outline` -- Table of contents with numbered items
- `divide` -- Section break with number and title
- `explain` -- Standard bullet points with optional sub-bullets
- `compare` -- Side-by-side comparison (2 sides)
- `categorize` -- 3+ parallel categories
- `measure` -- KPI/metric dashboard (3-4 cards)
- `visualize` -- Chart (column, bar, line, pie, area, doughnut)
- `tabulate` -- Data table with optional conditional highlighting
- `evaluate` -- Pros/cons analysis with advantages and challenges
- `sequence` -- Timeline/roadmap with milestones
- `emphasize` -- Big number or notable quote
- `illustrate` -- Image + text
- `summarize` -- Key takeaways with optional call-to-action

### Step 4: Content Quality Rules

- Always start with `open`, end with `summarize` or `close`
- For 3+ sections: add `outline` after `open` + `divide` before each section
- Limit bullet points to 5-7 per slide
- Keep titles under 60 characters
- Use `measure` when 3-4 KPIs are available
- Use `visualize` when time-series or categorical data is present
- Use `evaluate` when presenting options/alternatives
- Use `emphasize` for a single standout statistic or notable quote
- Cap at 20 slides maximum
- Every slide must have a clear, descriptive title
- Use specific numbers and metrics over vague statements

### Step 5: Write JSON and Generate PPTX

1. Determine the output path. Default is `./presentation.pptx` unless the user specifies otherwise.

2. Write the JSON specification **next to the output file** using the Write tool. If the output is `./presentation.pptx`, write the spec to `./presentation.spec.json`. This keeps them together for iteration and avoids `/tmp` being cleared on reboot.

```
Write the JSON to ./<name>.spec.json
```

3. Ensure python-pptx is installed:
```bash
python3 -c "import pptx" 2>/dev/null || pip3 install python-pptx
```

4. Find the script path and run generation:
```bash
SKILL_DIR="$(find ~/.claude/skills . -path '*/slides/scripts/generate_pptx.py' -print -quit 2>/dev/null | xargs dirname)"
python3 "$SKILL_DIR/generate_pptx.py" --input ./<name>.spec.json --output ./<name>.pptx
```

If the find command fails, try the project-local path:
```bash
python3 slides/scripts/generate_pptx.py --input ./<name>.spec.json --output ./<name>.pptx
```

### Step 6: Report Results

After successful generation:
- Report the file path and number of slides
- Briefly list the slide structure (e.g., "14 slides: cover, agenda, 3 sections with content/charts/KPIs, takeaways, closing")
- Report any warnings from the overflow/validation system (if any)
- Offer to refine specific slides, change the style, or adjust content

If generation fails, read the error output, fix the JSON specification, and re-run.

## Complete Example

User says: `/slides quarterly business review for Acme Corp, revenue $142M +18% YoY`

**Step 1**: Topic is "quarterly business review", company is "Acme Corp", data: revenue $142M, +18% YoY.

**Step 3**: Generate this JSON and write to `./acme_q3_review.spec.json`:

```json
{
  "metadata": {
    "title": "Quarterly Business Review",
    "company": "Acme Corp",
    "date": "Q3 2026",
    "confidentiality": "Confidential",
    "style": {"mood": "professional"}
  },
  "slides": [
    {"intent": "open", "title": "Q3 2026 Business Review", "subtitle": "Acme Corp"},
    {"intent": "outline", "title": "Agenda", "items": [
      {"text": "Financial Performance", "detail": "Revenue and key metrics"},
      {"text": "Market Analysis", "detail": "Trends and competition"},
      {"text": "Outlook", "detail": "Next steps and recommendations"}
    ]},
    {"intent": "divide", "title": "Financial Performance", "section_number": 1},
    {"intent": "measure", "title": "Key Metrics", "metrics": [
      {"label": "Revenue", "value": "$142M", "change": "+18%", "trend": "up"},
      {"label": "Growth", "value": "18%", "change": "+3pp", "trend": "up"},
      {"label": "Margin", "value": "72%", "change": "+2pp", "trend": "up"}
    ]},
    {"intent": "visualize", "title": "Revenue Trend", "chart": {
      "type": "column_clustered",
      "categories": ["Q1", "Q2", "Q3"],
      "series": [{"name": "Revenue ($M)", "values": [118, 130, 142]}]
    }},
    {"intent": "divide", "title": "Market Analysis", "section_number": 2},
    {"intent": "explain", "title": "Market Trends", "points": [
      {"text": "Enterprise segment driving growth", "subpoints": ["65% of new revenue"]},
      {"text": "Competitive landscape shifting"},
      {"text": "Regulatory changes ahead in H2"}
    ]},
    {"intent": "divide", "title": "Outlook", "section_number": 3},
    {"intent": "summarize", "title": "Key Takeaways", "takeaways": [
      "Revenue at $142M, up 18% YoY -- strong quarter",
      "Enterprise segment is the growth engine",
      "Need to address emerging competitive threats"
    ], "action": "Approve Q4 growth investment plan"},
    {"intent": "close", "title": "Thank You", "subtitle": "Questions?"}
  ]
}
```

**Step 5**: Run generation:
```bash
python3 slides/scripts/generate_pptx.py --input ./acme_q3_review.spec.json --output ./acme_q3_review.pptx
```

**Step 6**: "Generated `acme_q3_review.pptx` with 10 slides: cover, agenda, 3 sections (KPIs, chart, market analysis), takeaways, closing. No warnings."

## Style Selection

The rendering engine uses a style library extracted from real enterprise presentations. Style can be specified via the `metadata.style` object:

- `{"mood": "professional"}` -- conservative, clean design (default)
- `{"mood": "bold"}` -- high-contrast, vibrant accents
- `{"mood": "warm"}` -- earth tones, approachable feel
- `{"mood": "minimal"}` -- lots of white space, understated
- `{"palette": "palette-01-professional"}` -- exact palette ID
- `{"font": "Calibri"}` -- match by font family

See [references/style-guide.md](references/style-guide.md) for available palettes and typography patterns.

## Safety System

The generation pipeline includes automatic quality assurance:

1. **Overflow prevention** -- content that exceeds zone capacity is automatically adjusted (font reduction, spacing compression, content splitting across slides)
2. **Post-render validation** -- every shape is audited for overlaps, out-of-bounds, and text overflow, with corrective fixes applied automatically
3. **Warnings** -- any adjustments are reported so you can inform the user

You do not need to worry about content overflow. The engine handles it. Focus on generating good content with appropriate intents.

## Iteration

When the user asks to modify the presentation:

1. **Read** the existing spec: `Read ./<name>.spec.json` (the spec file next to the PPTX)
2. **Identify** what to change:
   - "Make slide 4 a chart instead" -> change that slide's `intent` and fields
   - "Add a comparison of options" -> insert a new `evaluate` slide at the right position
   - "Remove the timeline" -> delete the `sequence` slide
   - "Change the style to bold" -> update `metadata.style.mood`
   - "Fix the title on slide 3" -> update that slide's `title` field
3. **Modify** the JSON -- change only the affected slides, don't regenerate everything
4. **Write** the updated spec back to the same `.spec.json` path
5. **Re-run** the generation script with the same output path
6. **Report** what changed: "Updated slide 4 from bullets to chart, regenerated presentation"

For bulk changes (completely different topic or structure), regenerate the full spec instead of patching.
