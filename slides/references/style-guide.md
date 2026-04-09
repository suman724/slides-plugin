# Style Guide

The rendering engine uses a style library extracted from real enterprise presentations. Styles are resolved from the `metadata.style` object in the specification.

## How Style Resolution Works

1. **Exact ID match** -- specify `"palette": "palette-01-professional"` for a specific palette
2. **Mood match** -- specify `"mood": "professional"` and the engine picks the best matching palette
3. **Font match** -- specify `"font": "Calibri"` to match by font family
4. **Default** -- if nothing specified, the first palette (most common across source files) is used

## Available Palettes

Palettes are extracted from the style library and may vary as more source presentations are added. Current palettes:

| ID | Mood | Temperature | Primary | Accent | Sources |
|---|---|---|---|---|---|
| `palette-01-professional` | Professional | Cool | Navy `#44546A` | Amber `#ED7D31` | 28 files |
| `palette-02-professional` | Professional | Neutral | Black `#000000` | Teal `#007894` | 2 files |
| `palette-03-professional` | Professional | Neutral | Gray `#A7A7A7` | Red `#C0504D` | 2 files |
| `palette-04-professional` | Professional | Cool | Green `#5CFF86` | Purple `#7D2AE7` | 1 file |

**Note:** Currently all palettes have mood `"professional"`. This means `{"mood": "bold"}`, `{"mood": "warm"}`, and `{"mood": "minimal"}` will fall back to the default palette. Palette mood diversity improves as more source PPTX files with distinct color schemes are added to the pipeline.

## Available Typography Patterns

| ID | Font | Fallback | Body Size | Sources |
|---|---|---|---|---|
| `typo-arial` | Arial | Calibri | 12pt | 8 files |
| `typo-calibri` | Calibri | Arial | 14pt | 5 files |
| `typo-rubik` | Rubik | Bitter | -- * | 3 files |
| `typo-gill-sans-mt` | Gill Sans MT | Arial | -- * | 1 file |
| `typo-segoe-ui` | Segoe UI | Arial Black | -- * | 1 file |
| `typo-neue-haas-grotesk-text-pro` | Neue Haas Grotesk | Arial | -- * | 1 file |
| `typo-cambria` | Cambria | Times New Roman | 14pt | 1 file |
| `typo-inter-medium` | Inter Medium | Inter | 12pt | 1 file |
| `typo-kollektif-bold` | Kollektif Bold | Kollektif | 14pt | 1 file |

**Safe fonts** (universally installed): Arial, Calibri, Segoe UI, Verdana, Georgia, Cambria, Times New Roman, Gill Sans MT, Tahoma, Trebuchet MS, Helvetica.

For body text, the engine prefers safe fonts even if the typography pattern specifies an exotic font.

`*` These patterns lack a body text size in the library. The engine falls back to 14pt Calibri/Arial for body text when the pattern doesn't specify one. They are best used for their heading/display fonts while body text uses a safe default.

## Mood Keywords

| Mood | Best For | Visual Character |
|---|---|---|
| `professional` | Board meetings, investor decks, formal reviews | Conservative colors, clean layout |
| `bold` | Product launches, tech pitches, creative decks | High contrast, vibrant accents |
| `warm` | Team updates, culture presentations, social impact | Earth tones, approachable feel |
| `minimal` | Thought leadership, research, minimalist brands | Lots of white space, understated accents |

## Examples

**Default (professional):**
```json
{"metadata": {"title": "Q3 Review", "company": "Acme Corp"}}
```

**Specific mood:**
```json
{"metadata": {"title": "Product Launch", "style": {"mood": "bold"}}}
```

**Specific font:**
```json
{"metadata": {"title": "Research Report", "style": {"font": "Cambria"}}}
```

**Exact palette:**
```json
{"metadata": {"title": "Custom Deck", "style": {"palette": "palette-02-professional"}}}
```
