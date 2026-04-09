---
name: slides
description: Generate enterprise-quality PPTX presentations. Use when the user asks to create a presentation, make slides, generate a PowerPoint, build a deck, or mentions creating professional presentations, board decks, strategy presentations, or slide generation.
argument-hint: <topic or detailed context>
allowed-tools: Bash(python3 *) Read Write
---

# Enterprise PPTX Presentation Generator

Generate professional, enterprise-quality PowerPoint presentations from user-provided context. Output is a `.pptx` file created entirely from code using Python and python-pptx.

## Workflow

Follow these steps exactly:

### Step 1: Parse User Input

Read `$ARGUMENTS` to understand the topic, context, constraints, and any specific data provided. Look for:
- Topic or title
- Data points, metrics, KPIs
- Structural cues ("compare X and Y", "timeline for...", "key findings")
- Theme preference (`--theme corporate_blue|modern_dark|minimal`)
- Output path (`--output path/to/file.pptx`)

### Step 2: Determine Content Augmentation Level

- **Minimal input** (just a topic like "quarterly review"): Generate a complete 10-12 slide deck with plausible structure and content.
- **Structured input** (topic + some data points): Use provided data as anchors, fill surrounding context. Generate 8-12 slides.
- **Detailed input** (full outline or pasted document): Structure and format faithfully. Add agenda/closing slides if missing.

### Step 3: Generate JSON Slide Specification

Create a complete JSON specification following the schema in [references/json-schema.md](references/json-schema.md). The JSON has two sections:

**metadata**: title, subtitle, author, company, date, confidentiality, theme, output_path
**slides**: array of slide objects, each with a `type` and type-specific fields

Available slide types (see [references/slide-types.md](references/slide-types.md) for details):
- `title` - Cover/opening slide
- `agenda` - Table of contents with numbered items
- `section_divider` - Section break with number and title
- `content` - Standard bullet slide
- `two_column` - Side-by-side content
- `three_column` - Triple content columns
- `chart` - Data visualization (column, bar, line, pie, area, doughnut)
- `table` - Formatted data table with conditional highlighting
- `key_metrics` - KPI dashboard with 3-4 metric cards
- `comparison` - Pros/cons side-by-side with check/cross marks
- `timeline` - Horizontal roadmap with milestones
- `takeaway` - Key findings with numbered points and call-to-action
- `quote` - Large quote with attribution
- `image_with_text` - Image placeholder + text
- `big_number` - Single standout statistic
- `closing` - Thank you/end slide

### Step 4: Content Quality Rules

Follow these rules when generating slide content:
- Always start with a `title` slide and end with a `takeaway` or `closing` slide
- For 3+ sections, add an `agenda` slide after the title and `section_divider` slides before each section
- Limit bullets to 5-7 per slide; split across slides if needed
- Use `key_metrics` when 3-4 KPIs are available
- Use `chart` when time-series or categorical data is present
- Use `comparison` when presenting options or alternatives
- Use `big_number` for a single standout statistic
- Cap at 20 slides maximum
- Every slide must have a clear, descriptive title
- Use specific numbers and metrics over vague statements
- Speaker-ready: content should be presentation-appropriate, not document-style

### Step 5: Write JSON and Generate PPTX

1. Write the JSON specification to a temporary file:

```python
import json, tempfile
spec = { ... }  # your generated specification
with open('/tmp/slides_spec.json', 'w') as f:
    json.dump(spec, f, indent=2)
```

2. Ensure python-pptx is installed:
```bash
python3 -c "import pptx" 2>/dev/null || pip3 install python-pptx
```

3. Run the generation script:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_pptx.py --input /tmp/slides_spec.json --output <output_path>
```

Default output path is `./presentation.pptx` unless the user specifies otherwise.

### Step 6: Report Results

After successful generation:
- Report the file path
- Summarize the deck structure (number of slides, sections covered)
- Offer to refine specific slides, change the theme, or adjust content

If generation fails, read the error output and fix the JSON specification.

## Themes

Three enterprise themes are available (see [references/design-system.md](references/design-system.md)):

- **`corporate_blue`** (default): Navy/blue palette with amber accents. Professional and conservative. Best for board meetings, investor presentations, and formal reviews.
- **`modern_dark`**: Near-black backgrounds with coral accents. Bold and contemporary. Best for product launches, tech presentations, and creative pitches.
- **`minimal`**: Clean white with blue accents. Understated and elegant. Best for thought leadership, research presentations, and minimalist brands.

Select based on user cues or explicitly stated preference. Default to `corporate_blue`.

## Iteration

When the user asks to modify the presentation:
1. Read the existing JSON spec from the temp file or regenerate it
2. Make targeted changes to specific slides
3. Re-run the generation script
4. Report what changed

This allows rapid iteration without regenerating the entire deck.
