#!/usr/bin/env python3
"""Generate gallery PPTX files for visual verification.

Creates a presentation with every intent type to visually test rendering quality.
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'slides', 'scripts'))

import style_resolver
style_resolver._cached_library = None

from generate_pptx import generate


GALLERY_SPEC = {
    "metadata": {
        "title": "Gallery: All Intents",
        "company": "Acme Corp",
        "confidentiality": "Internal",
        "date": "April 2026",
    },
    "slides": [
        {"intent": "open", "title": "Gallery: All 15 Intents", "subtitle": "Visual Verification Deck"},
        {"intent": "outline", "title": "Agenda", "items": [
            {"text": "Content Intents", "detail": "explain, compare, categorize"},
            {"text": "Data Intents", "detail": "measure, visualize, tabulate"},
            {"text": "Analysis Intents", "detail": "evaluate, sequence, summarize"},
            {"text": "Special Intents", "detail": "emphasize, illustrate"},
        ]},
        {"intent": "divide", "title": "Content Intents", "subtitle": "explain, compare, categorize", "section_number": 1},
        {"intent": "explain", "title": "Key Market Trends", "points": [
            {"text": "Total addressable market grew 12% YoY to $4.2B", "subpoints": [
                "Enterprise segment accounts for 65% of growth",
                "SMB segment showing early signs of recovery",
            ]},
            {"text": "Competitor X launched adjacent product in Q2"},
            {"text": "Regulatory changes expected in H2 2026", "subpoints": [
                "New compliance framework will require certification",
            ]},
        ]},
        {"intent": "compare", "title": "Revenue vs. Plan", "sides": [
            {"heading": "Performance", "points": ["Revenue: $142M (+18% YoY)", "Gross margin: 72%", "Free cash flow: $28M"]},
            {"heading": "Commentary", "points": ["Enterprise pipeline strong", "SMB churn at 4.2%", "PLG showing results"]},
        ]},
        {"intent": "categorize", "title": "Implementation Phases", "sides": [
            {"heading": "Phase 1", "points": ["Foundation", "Core features", "Team setup"]},
            {"heading": "Phase 2", "points": ["Advanced features", "Integration", "Testing"]},
            {"heading": "Phase 3", "points": ["Optimization", "Scale", "Launch"]},
        ]},
        {"intent": "divide", "title": "Data Intents", "subtitle": "measure, visualize, tabulate", "section_number": 2},
        {"intent": "measure", "title": "Key Performance Indicators", "metrics": [
            {"label": "ARR", "value": "$568M", "change": "+18%", "trend": "up"},
            {"label": "NRR", "value": "118%", "change": "+3pp", "trend": "up"},
            {"label": "CAC Payback", "value": "14mo", "change": "-2mo", "trend": "up"},
            {"label": "Churn", "value": "4.2%", "change": "+0.8pp", "trend": "down"},
        ]},
        {"intent": "visualize", "title": "Revenue by Quarter", "chart": {
            "type": "column_clustered",
            "categories": ["Q1 '25", "Q2 '25", "Q3 '25", "Q4 '25", "Q1 '26", "Q2 '26", "Q3 '26"],
            "series": [
                {"name": "Revenue ($M)", "values": [98, 105, 112, 120, 128, 135, 142]},
                {"name": "Target ($M)", "values": [100, 108, 115, 122, 130, 138, 145]},
            ],
        }, "note": "Q3 revenue within 2% of target despite macro headwinds"},
        {"intent": "tabulate", "title": "P&L Summary ($M)", "columns": ["Metric", "Q3 Actual", "Q3 Plan", "Variance", "YoY"],
         "rows": [
            ["Revenue", "142", "145", "-2%", "+18%"],
            ["Gross Profit", "102", "102", "0%", "+20%"],
            ["EBITDA", "38", "40", "-5%", "+25%"],
            ["Net Income", "22", "24", "-8%", "+30%"],
         ], "highlight_rules": [
            {"column": 3, "condition": "negative", "color": "red"},
            {"column": 4, "condition": "positive", "color": "green"},
         ]},
        {"intent": "divide", "title": "Analysis Intents", "subtitle": "evaluate, sequence, summarize", "section_number": 3},
        {"intent": "evaluate", "title": "Strategic Options", "options": [
            {"heading": "Organic Growth", "advantages": ["Lower risk", "Preserves cash", "Team focus"], "challenges": ["Slower capture", "Competitor gap"]},
            {"heading": "Acquisition", "advantages": ["Immediate share", "Tech synergies", "Talent"], "challenges": ["Integration risk", "$200M capital"]},
        ]},
        {"intent": "sequence", "title": "Implementation Roadmap", "steps": [
            {"when": "Q4 2026", "what": "Board Approval", "detail": "Final decision"},
            {"when": "Q1 2027", "what": "Execution", "detail": "Team formation"},
            {"when": "Q2 2027", "what": "Phase 1", "detail": "Initial milestone"},
            {"when": "Q4 2027", "what": "Value Realization", "detail": "Synergy capture"},
        ]},
        {"intent": "summarize", "title": "Key Takeaways", "takeaways": [
            "Q3 performance strong despite macro headwinds; within 2% of plan",
            "Enterprise pipeline robust; SMB churn requires immediate action",
            "Board decision on strategic direction needed by Q4 2026",
        ], "action": "Approve formation of Strategic Evaluation Committee"},
        {"intent": "divide", "title": "Special Intents", "subtitle": "emphasize, illustrate", "section_number": 4},
        {"intent": "emphasize", "title": "Market Opportunity", "emphasis": {
            "type": "number", "value": "$4.2B", "label": "Total Addressable Market",
            "context": "Growing at 12% annually with enterprise segment driving 65% of new demand",
        }},
        {"intent": "emphasize", "emphasis": {
            "type": "quote",
            "text": "The best way to predict the future is to create it.",
            "attribution": "Peter Drucker",
        }},
        {"intent": "illustrate", "title": "Product Screenshot", "points": [
            {"text": "New dashboard provides real-time visibility"},
            {"text": "Customizable widgets for each team"},
            {"text": "Mobile-responsive design"},
        ]},
        {"intent": "close", "title": "Thank You", "subtitle": "Questions & Discussion", "contact": "strategy@acme.com"},
    ],
}


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "gallery")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "gallery_all_intents.pptx")
    prs, warnings = generate(GALLERY_SPEC)
    prs.save(output_path)

    print(f"Gallery saved to: {output_path}")
    print(f"  Slides: {len(prs.slides)}")
    if warnings:
        print(f"  Warnings: {len(warnings)}")
        for w in warnings:
            print(f"    {w}")
    else:
        print("  Warnings: none")


if __name__ == "__main__":
    main()
