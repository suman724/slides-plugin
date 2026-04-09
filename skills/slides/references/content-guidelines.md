# Content Guidelines

## Augmentation Levels

### Level 1: Minimal Input
The user provides just a topic (e.g., `/slides quarterly review`).

- Generate a complete 10-12 slide deck with plausible structure
- Follow the standard consulting deck template: Title -> Agenda -> Sections -> Summary -> Closing
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
- Focus on layout selection and visual hierarchy
- Add agenda/closing if missing
- Generate as many slides as content warrants

## Content Quality Rules

1. **Every slide needs a clear title** - descriptive, not generic ("Revenue Growth Drivers" not "Slide 5")
2. **5-7 bullets max per slide** - if you have more, split across slides
3. **Be specific** - use numbers, dates, and names instead of vague statements
4. **Parallel structure** - all bullets at the same level should follow the same grammatical pattern
5. **Action-oriented** - prefer "Revenue grew 18% to $142M" over "Revenue was $142M"
6. **No walls of text** - slides are visual aids, not documents

## Deck Structure Patterns

### Executive Review (10-15 slides)
Title -> Agenda -> Section: Performance (KPIs, charts) -> Section: Analysis (content, comparison) -> Section: Outlook (timeline, takeaway) -> Closing

### Project Update (8-12 slides)
Title -> Agenda -> Status Overview (key_metrics) -> Progress Detail (content slides) -> Risks/Issues (two_column) -> Next Steps (takeaway) -> Closing

### Strategy Presentation (12-18 slides)
Title -> Agenda -> Market Context (content, big_number) -> Current State (charts, tables) -> Strategic Options (comparison) -> Recommendation (takeaway) -> Implementation (timeline) -> Closing

### Product Launch (8-12 slides)
Title -> Problem Statement (big_number or quote) -> Solution (content, image_with_text) -> Key Features (three_column) -> Market Opportunity (chart) -> Go-to-Market (timeline) -> Ask (takeaway) -> Closing

## Layout Selection Guide

| Content Type | Recommended Layout |
|---|---|
| Opening | `title` |
| Table of contents | `agenda` |
| Section break | `section_divider` |
| Bullet points | `content` |
| Side-by-side info | `two_column` |
| Three categories | `three_column` |
| Trends over time | `chart` (line) |
| Category comparison | `chart` (column) |
| Composition/share | `chart` (pie/doughnut) |
| Detailed data | `table` |
| 3-4 KPIs | `key_metrics` |
| Options evaluation | `comparison` |
| Project plan | `timeline` |
| Summary | `takeaway` |
| Impactful stat | `big_number` |
| Notable quote | `quote` |
| Visual + text | `image_with_text` |
| End | `closing` |
