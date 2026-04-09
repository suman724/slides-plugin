#!/usr/bin/env python3
"""Generate a gallery PPTX with every slide type in every theme for visual testing."""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'slides', 'scripts'))

from generate_pptx import generate
from pptx import Presentation

# Complete spec exercising every slide type
GALLERY_SLIDES = [
    {
        "type": "title",
        "title": "Gallery: {theme_name}",
        "subtitle": "Visual test of all slide layouts",
        "date": "April 2026",
        "confidentiality": "Internal"
    },
    {
        "type": "agenda",
        "title": "Agenda",
        "items": [
            {"number": 1, "text": "Content Layouts", "subtext": "Standard content delivery slides"},
            {"number": 2, "text": "Data Layouts", "subtext": "Charts, tables, and metrics"},
            {"number": 3, "text": "Analysis Layouts", "subtext": "Comparison, timeline, takeaway"},
            {"number": 4, "text": "Special Layouts", "subtext": "Quote, big number, image"}
        ]
    },
    {
        "type": "section_divider",
        "section_number": 1,
        "title": "Content Layouts",
        "subtitle": "Standard content delivery slides"
    },
    {
        "type": "content",
        "title": "Content Slide Example",
        "body": [
            {"type": "bullet", "text": "First main point with important information", "level": 0},
            {"type": "bullet", "text": "Supporting detail for first point", "level": 1},
            {"type": "bullet", "text": "Another supporting detail", "level": 1},
            {"type": "bullet", "text": "Second main point with key data", "level": 0},
            {"type": "bullet", "text": "Third main point about outcomes", "level": 0},
            {"type": "bullet", "text": "Additional context for third point", "level": 1}
        ]
    },
    {
        "type": "two_column",
        "title": "Two Column Layout",
        "left": {
            "heading": "Current State",
            "body": [
                {"type": "bullet", "text": "Existing capability A", "level": 0},
                {"type": "bullet", "text": "Existing capability B", "level": 0},
                {"type": "bullet", "text": "Known limitation", "level": 0}
            ]
        },
        "right": {
            "heading": "Future State",
            "body": [
                {"type": "bullet", "text": "Enhanced capability A", "level": 0},
                {"type": "bullet", "text": "New capability C", "level": 0},
                {"type": "bullet", "text": "Limitation resolved", "level": 0}
            ]
        }
    },
    {
        "type": "three_column",
        "title": "Three Column Layout",
        "columns": [
            {
                "heading": "Phase 1",
                "body": [
                    {"type": "bullet", "text": "Foundation work", "level": 0},
                    {"type": "bullet", "text": "Core features", "level": 0}
                ]
            },
            {
                "heading": "Phase 2",
                "body": [
                    {"type": "bullet", "text": "Advanced features", "level": 0},
                    {"type": "bullet", "text": "Integration", "level": 0}
                ]
            },
            {
                "heading": "Phase 3",
                "body": [
                    {"type": "bullet", "text": "Optimization", "level": 0},
                    {"type": "bullet", "text": "Scale", "level": 0}
                ]
            }
        ]
    },
    {
        "type": "section_divider",
        "section_number": 2,
        "title": "Data Layouts",
        "subtitle": "Charts, tables, and metrics"
    },
    {
        "type": "chart",
        "title": "Column Chart Example",
        "chart_type": "column_clustered",
        "categories": ["Q1", "Q2", "Q3", "Q4"],
        "series": [
            {"name": "2025", "values": [100, 110, 120, 130]},
            {"name": "2026", "values": [115, 125, 135, 145]}
        ],
        "annotation": "Consistent quarter-over-quarter growth across both years"
    },
    {
        "type": "chart",
        "title": "Line Chart Example",
        "chart_type": "line_markers",
        "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "series": [
            {"name": "Users (K)", "values": [12, 15, 18, 22, 28, 35]},
            {"name": "Target (K)", "values": [14, 17, 20, 24, 28, 32]}
        ]
    },
    {
        "type": "table",
        "title": "Table Layout Example",
        "columns": ["Region", "Revenue", "Growth", "Margin"],
        "rows": [
            ["North America", "$85M", "+15%", "72%"],
            ["Europe", "$42M", "+22%", "68%"],
            ["Asia Pacific", "$28M", "+35%", "65%"],
            ["Rest of World", "$12M", "+18%", "60%"]
        ],
        "highlight_rules": [
            {"column": 2, "condition": "positive", "color": "green"}
        ]
    },
    {
        "type": "key_metrics",
        "title": "Key Metrics Dashboard",
        "metrics": [
            {"label": "Revenue", "value": "$167M", "delta": "+22%", "direction": "up"},
            {"label": "Customers", "value": "2,450", "delta": "+340", "direction": "up"},
            {"label": "NPS", "value": "72", "delta": "+8", "direction": "up"},
            {"label": "Churn", "value": "3.1%", "delta": "+0.5pp", "direction": "down"}
        ]
    },
    {
        "type": "section_divider",
        "section_number": 3,
        "title": "Analysis Layouts",
        "subtitle": "Comparison, timeline, takeaway"
    },
    {
        "type": "comparison",
        "title": "Comparison Layout",
        "left": {
            "heading": "Build In-House",
            "pros": ["Full control", "Custom fit", "IP ownership"],
            "cons": ["12-18 month timeline", "Hiring required"]
        },
        "right": {
            "heading": "Buy / Partner",
            "pros": ["Faster time to market", "Proven solution"],
            "cons": ["Vendor dependency", "Less customization", "Ongoing costs"]
        }
    },
    {
        "type": "timeline",
        "title": "Timeline Layout",
        "milestones": [
            {"date": "Q1 2026", "label": "Discovery", "detail": "Requirements and research"},
            {"date": "Q2 2026", "label": "Design", "detail": "Architecture and prototyping"},
            {"date": "Q3 2026", "label": "Build", "detail": "Core development sprint"},
            {"date": "Q4 2026", "label": "Launch", "detail": "GA release and rollout"}
        ]
    },
    {
        "type": "takeaway",
        "title": "Key Takeaways",
        "points": [
            "First important conclusion from the analysis",
            "Second key finding that drives the recommendation",
            "Third point that supports the proposed next steps"
        ],
        "call_to_action": "Approve the proposed roadmap and allocate Q1 budget"
    },
    {
        "type": "big_number",
        "title": "Market Opportunity",
        "value": "$12.5B",
        "label": "Total Addressable Market by 2028",
        "context": "Growing at 18% CAGR driven by enterprise digital transformation"
    },
    {
        "type": "quote",
        "title": "",
        "quote": "Innovation distinguishes between a leader and a follower.",
        "attribution": "Steve Jobs"
    },
    {
        "type": "closing",
        "title": "Thank You",
        "subtitle": "Questions & Discussion",
        "contact": "team@company.com"
    }
]


def generate_gallery():
    themes = ["corporate_blue", "modern_dark", "minimal"]
    output_dir = os.path.join(os.path.dirname(__file__), "gallery")
    os.makedirs(output_dir, exist_ok=True)

    for theme_name in themes:
        # Customize title slide with theme name
        slides = []
        for s in GALLERY_SLIDES:
            slide = dict(s)
            if slide["type"] == "title":
                slide["title"] = f"Gallery: {theme_name}"
            slides.append(slide)

        spec = {
            "metadata": {
                "title": f"Gallery - {theme_name}",
                "company": "Test Corp",
                "confidentiality": "Internal",
                "theme": theme_name,
            },
            "slides": slides,
        }

        prs = generate(spec)
        output_path = os.path.join(output_dir, f"gallery_{theme_name}.pptx")
        prs.save(output_path)
        print(f"Generated: {output_path} ({len(slides)} slides)")


if __name__ == "__main__":
    generate_gallery()
