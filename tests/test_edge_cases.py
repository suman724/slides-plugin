"""Edge-case test suite for the quality assurance safety system.

Every test creates a deliberately tricky slide spec, generates a PPTX
through the full pipeline (overflow -> render -> validate+fix), and
asserts zero unresolved issues.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'slides', 'scripts'))

# Clear cached library between test files
import style_resolver
style_resolver._cached_library = None

from generate_pptx import generate
from layout_validator import validate_and_fix, validate_presentation


def _generate_and_validate(spec):
    """Helper: generate PPTX and assert zero unresolved validation issues."""
    prs, warnings = generate(spec)
    issues = validate_presentation(prs)
    unresolved = [i for i in issues if not i.auto_fixed]
    return prs, warnings, unresolved


def _make_spec(slides):
    """Wrap slides in a minimal spec."""
    return {
        "metadata": {"title": "Test", "company": "TestCo", "confidentiality": "Internal"},
        "slides": slides,
    }


# ---------------------------------------------------------------------------
# Bullet tests
# ---------------------------------------------------------------------------

class TestBulletOverflow:
    def test_12_bullets(self):
        """12 bullet points should be split or compressed, with no overlaps."""
        spec = _make_spec([{
            "intent": "explain",
            "title": "Many Bullets",
            "points": [{"text": f"Bullet point number {i+1} with enough text to be meaningful"} for i in range(12)],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0, f"Unresolved: {unresolved}"

    def test_15_bullets_with_subpoints(self):
        """15 bullets with subpoints -- must split across slides."""
        spec = _make_spec([{
            "intent": "explain",
            "title": "Lots of Detail",
            "points": [
                {"text": f"Main point {i+1}", "subpoints": [f"Sub-detail {i+1}.{j+1}" for j in range(2)]}
                for i in range(15)
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0

    def test_very_long_bullet_text(self):
        """Single bullet with 200+ character text should be truncated or wrapped."""
        long_text = "This is a very long bullet point that goes on and on about the market conditions and strategic implications " * 3
        spec = _make_spec([{
            "intent": "explain",
            "title": "Long Text",
            "points": [{"text": long_text}],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0


# ---------------------------------------------------------------------------
# Title tests
# ---------------------------------------------------------------------------

class TestTitleOverflow:
    def test_long_title_120_chars(self):
        """120-character title should be reduced or truncated, no right-edge overflow."""
        title = "A" * 120
        spec = _make_spec([{
            "intent": "explain",
            "title": title,
            "points": [{"text": "Content here"}],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0

    def test_title_with_special_chars(self):
        """Title with unicode characters."""
        spec = _make_spec([{
            "intent": "explain",
            "title": "Revenue Growth: Q3 2026 \u2014 Strategic Analysis & Recommendations (Draft)",
            "points": [{"text": "Test"}],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0


# ---------------------------------------------------------------------------
# Metrics tests
# ---------------------------------------------------------------------------

class TestMetricsOverflow:
    def test_8_metrics(self):
        """8 KPIs should be split into multiple slides."""
        spec = _make_spec([{
            "intent": "measure",
            "title": "All KPIs",
            "metrics": [
                {"label": f"KPI {i+1}", "value": f"${i*10}M", "change": f"+{i}%", "trend": "up"}
                for i in range(8)
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(prs.slides) >= 2, "Should split into multiple slides"
        assert len(unresolved) == 0

    def test_5_metrics(self):
        """5 KPIs should use grid layout, not split."""
        spec = _make_spec([{
            "intent": "measure",
            "title": "Five KPIs",
            "metrics": [
                {"label": f"KPI {i+1}", "value": f"${i*10}M", "change": f"+{i}%", "trend": "up"}
                for i in range(5)
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0


# ---------------------------------------------------------------------------
# Table tests
# ---------------------------------------------------------------------------

class TestTableOverflow:
    def test_wide_table_10_columns(self):
        """Table with 10 columns should fit with reduced fonts."""
        spec = _make_spec([{
            "intent": "tabulate",
            "title": "Wide Table",
            "columns": [f"Col {i+1}" for i in range(10)],
            "rows": [[f"R{r}C{c}" for c in range(10)] for r in range(5)],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0

    def test_tall_table_20_rows(self):
        """Table with 20 rows should be split."""
        spec = _make_spec([{
            "intent": "tabulate",
            "title": "Tall Table",
            "columns": ["Name", "Value", "Growth"],
            "rows": [[f"Item {i+1}", f"${i*5}M", f"+{i}%"] for i in range(20)],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(prs.slides) >= 2, "Should split into multiple slides"
        assert len(unresolved) == 0


# ---------------------------------------------------------------------------
# Chart tests
# ---------------------------------------------------------------------------

class TestChartOverflow:
    def test_20_chart_categories(self):
        """Chart with 20 categories should switch type or truncate."""
        spec = _make_spec([{
            "intent": "visualize",
            "title": "Many Categories",
            "chart": {
                "type": "column_clustered",
                "categories": [f"Cat {i+1}" for i in range(20)],
                "series": [{"name": "Values", "values": list(range(20))}],
            },
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0


# ---------------------------------------------------------------------------
# Timeline tests
# ---------------------------------------------------------------------------

class TestTimelineOverflow:
    def test_10_milestones(self):
        """Timeline with 10 milestones should compress labels."""
        spec = _make_spec([{
            "intent": "sequence",
            "title": "Long Roadmap",
            "steps": [
                {"when": f"Q{(i%4)+1} {2026 + i//4}", "what": f"Milestone {i+1}", "detail": "Details here"}
                for i in range(10)
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0

    def test_15_milestones(self):
        """15 milestones should be split into 2 timeline slides."""
        spec = _make_spec([{
            "intent": "sequence",
            "title": "Very Long Roadmap",
            "steps": [
                {"when": f"M{i+1}", "what": f"Step {i+1}", "detail": f"Detail {i+1}"}
                for i in range(15)
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(prs.slides) >= 2, "Should split into multiple slides"
        assert len(unresolved) == 0


# ---------------------------------------------------------------------------
# Compare / Evaluate tests
# ---------------------------------------------------------------------------

class TestCompareOverflow:
    def test_3_compare_options(self):
        """Compare with 3 sides should upgrade to 3-column."""
        spec = _make_spec([{
            "intent": "compare",
            "title": "Three Options",
            "sides": [
                {"heading": f"Option {c}", "points": [f"Point {i}" for i in range(3)]}
                for c in "ABC"
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0

    def test_5_evaluate_options(self):
        """Evaluate with 5 options should split into multiple slides."""
        spec = _make_spec([{
            "intent": "evaluate",
            "title": "Many Options",
            "options": [
                {"heading": f"Option {i+1}", "advantages": ["Pro 1", "Pro 2"], "challenges": ["Con 1"]}
                for i in range(5)
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(prs.slides) >= 2, "Should split into multiple slides"
        assert len(unresolved) == 0


# ---------------------------------------------------------------------------
# Agenda tests
# ---------------------------------------------------------------------------

class TestAgendaOverflow:
    def test_12_agenda_items(self):
        """Agenda with 12 items should compress or split."""
        spec = _make_spec([{
            "intent": "outline",
            "title": "Big Agenda",
            "items": [
                {"text": f"Topic {i+1}", "detail": f"Covering aspect {i+1} of the strategy"}
                for i in range(12)
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0


# ---------------------------------------------------------------------------
# All intents tests
# ---------------------------------------------------------------------------

class TestAllIntents:
    def test_all_intents_moderate(self):
        """One slide per intent with moderate content -- all should pass."""
        slides = [
            {"intent": "open", "title": "Test Deck", "subtitle": "Subtitle"},
            {"intent": "outline", "title": "Agenda", "items": [
                {"text": "Topic 1", "detail": "Detail 1"},
                {"text": "Topic 2", "detail": "Detail 2"},
            ]},
            {"intent": "divide", "title": "Section 1", "subtitle": "Details", "section_number": 1},
            {"intent": "explain", "title": "Content", "points": [
                {"text": "Point 1", "subpoints": ["Sub 1"]},
                {"text": "Point 2"},
            ]},
            {"intent": "compare", "title": "Compare", "sides": [
                {"heading": "A", "points": ["A1", "A2"]},
                {"heading": "B", "points": ["B1", "B2"]},
            ]},
            {"intent": "visualize", "title": "Chart", "chart": {
                "type": "column_clustered",
                "categories": ["Q1", "Q2", "Q3"],
                "series": [{"name": "Rev", "values": [10, 20, 30]}],
            }},
            {"intent": "measure", "title": "KPIs", "metrics": [
                {"label": "ARR", "value": "$100M", "change": "+10%", "trend": "up"},
                {"label": "NRR", "value": "110%", "change": "+5%", "trend": "up"},
            ]},
            {"intent": "tabulate", "title": "Table", "columns": ["A", "B"], "rows": [["1", "2"], ["3", "4"]]},
            {"intent": "evaluate", "title": "Options", "options": [
                {"heading": "Opt 1", "advantages": ["Pro"], "challenges": ["Con"]},
                {"heading": "Opt 2", "advantages": ["Pro"], "challenges": ["Con"]},
            ]},
            {"intent": "sequence", "title": "Timeline", "steps": [
                {"when": "Q1", "what": "Start", "detail": "Begin"},
                {"when": "Q4", "what": "End", "detail": "Finish"},
            ]},
            {"intent": "emphasize", "title": "Big Number", "emphasis": {
                "type": "number", "value": "$5B", "label": "TAM", "context": "Growing fast",
            }},
            {"intent": "emphasize", "emphasis": {
                "type": "quote", "text": "Innovation matters.", "attribution": "Someone",
            }},
            {"intent": "summarize", "title": "Summary", "takeaways": ["Key point 1", "Key point 2"],
             "action": "Next step"},
            {"intent": "close", "title": "Thank You", "subtitle": "Questions?", "contact": "a@b.com"},
        ]
        spec = _make_spec(slides)
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0, f"Unresolved: {[str(i) for i in unresolved]}"

    def test_all_intents_heavy(self):
        """One slide per intent with maximum content -- overflow + validator should handle."""
        slides = [
            {"intent": "open", "title": "A" * 80, "subtitle": "B" * 100},
            {"intent": "outline", "title": "Agenda", "items": [
                {"text": f"Topic {i+1}", "detail": f"Very detailed description of topic {i+1}"} for i in range(10)
            ]},
            {"intent": "divide", "title": "A" * 60, "subtitle": "B" * 80, "section_number": 1},
            {"intent": "explain", "title": "Content", "points": [
                {"text": f"Major point {i+1} with substantial detail", "subpoints": [f"Sub {j}" for j in range(3)]}
                for i in range(10)
            ]},
            {"intent": "compare", "title": "Compare", "sides": [
                {"heading": f"Option {c}", "points": [f"Detail {i}" for i in range(8)]}
                for c in "ABCD"
            ]},
            {"intent": "visualize", "title": "Chart", "chart": {
                "type": "column_clustered",
                "categories": [f"Cat {i}" for i in range(18)],
                "series": [{"name": "S1", "values": list(range(18))}],
            }},
            {"intent": "measure", "title": "KPIs", "metrics": [
                {"label": f"M{i}", "value": f"${i}M", "change": f"+{i}%", "trend": "up"} for i in range(7)
            ]},
            {"intent": "tabulate", "title": "Table", "columns": [f"C{i}" for i in range(8)],
             "rows": [[f"R{r}C{c}" for c in range(8)] for r in range(15)]},
            {"intent": "evaluate", "title": "Options", "options": [
                {"heading": f"Opt {i}", "advantages": ["P1", "P2", "P3"], "challenges": ["C1", "C2"]}
                for i in range(4)
            ]},
            {"intent": "sequence", "title": "Timeline", "steps": [
                {"when": f"M{i}", "what": f"Step {i}", "detail": f"Detail {i}"} for i in range(12)
            ]},
            {"intent": "emphasize", "title": "X" * 80, "emphasis": {
                "type": "number", "value": "$999B", "label": "Y" * 60, "context": "Z" * 150,
            }},
            {"intent": "summarize", "title": "Summary", "takeaways": [f"Takeaway {i}" for i in range(8)],
             "action": "A very long call to action that might not fit in a single line"},
            {"intent": "close", "title": "Thank You", "subtitle": "S" * 80, "contact": "email@company.com"},
        ]
        spec = _make_spec(slides)
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0, f"Unresolved: {[str(i) for i in unresolved]}"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_content(self):
        """Slides with minimal/empty fields should not crash."""
        slides = [
            {"intent": "open", "title": ""},
            {"intent": "explain", "title": "", "points": []},
            {"intent": "explain", "title": "Title Only"},
            {"intent": "close", "title": ""},
        ]
        spec = _make_spec(slides)
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0

    def test_unicode_content(self):
        """Titles and bullets with CJK, emoji, accents should render."""
        spec = _make_spec([{
            "intent": "explain",
            "title": "Analyse des march\u00e9s \u2014 \u6982\u8981",
            "points": [
                {"text": "Caf\u00e9 growth in \u00cele-de-France: +15%"},
                {"text": "\u65e5\u672c\u5e02\u5834\u306e\u52d5\u5411\u3068\u4eca\u5f8c\u306e\u5c55\u671b"},
                {"text": "M\u00e4rkte in Deutschland expandieren"},
            ],
        }])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(unresolved) == 0

    def test_single_slide_deck(self):
        """A deck with just one slide should work."""
        spec = _make_spec([{"intent": "open", "title": "Solo Slide"}])
        prs, warnings, unresolved = _generate_and_validate(spec)
        assert len(prs.slides) == 1
        assert len(unresolved) == 0
