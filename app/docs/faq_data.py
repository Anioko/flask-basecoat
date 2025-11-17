"""Data builders for FAQ block variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

FaqVariant = Dict[str, object]

_FAQ_DEFAULT: FaqVariant = {
    "eyebrow": "FAQs",
    "headline": "Answers for Basecoat UI teams",
    "description": "Everything product, design, and engineering leaders ask while rolling out shadcn-compatible Basecoat patterns.",
    "meta": "Don’t see what you need? Contact support for a tailored walkthrough.",
    "list": [],
}

_FAQ_BLUEPRINTS: Dict[str, FaqVariant] = {
    "faq-01": {
        "layout": "two-column",
        "list": [
            {
                "question": "How do we migrate from Semantic UI?",
                "answer": "Use the migration kit included with Basecoat UI—map legacy classes to modern utilities and ship without downtime.",
            },
            {
                "question": "Does Basecoat work with dark mode?",
                "answer": "Yes. Each block ships with balanced dark mode tokens that mirror the shadcn/ui reference.",
            },
            {
                "question": "Can we customise tokens?",
                "answer": "Override the Tailwind config or update the Basecoat token layer to match your brand palette.",
            },
            {
                "question": "What browsers do you support?",
                "answer": "We target the shadcn support matrix: latest Chrome, Edge, Firefox, and Safari releases.",
            },
        ],
        "cta": {"label": "Read migration guide", "url": "#"},
    },
    "faq-02": {
        "layout": "accordion",
        "accordion": [
            {
                "question": "How are new blocks released?",
                "answer": "We track ui.shadcn.com weekly. New Basecoat variants release every Friday with changelog notes.",
            },
            {
                "question": "Do you offer design tokens?",
                "answer": "Yes—download Figma libraries and JSON token exports from the Basecoat registry.",
            },
            {
                "question": "Is there enterprise support?",
                "answer": "Scale plans include a dedicated channel plus quarterly design reviews.",
            },
        ],
        "support": {
            "title": "Need a live walkthrough?",
            "description": "Book time with the Basecoat crew to align stakeholders and unblock delivery teams.",
            "actions": [
                {"label": "Schedule onboarding", "style": "primary"},
                {"label": "Join Slack", "style": "ghost"},
            ],
        },
    },
    "faq-03": {
        "layout": "cards",
        "list": [
            {
                "question": "How do we test docs pages?",
                "answer": "Run pytest with the docs suite: it asserts block coverage and legacy copy expectations.",
            },
            {
                "question": "Can we add custom categories?",
                "answer": "Update app/docs/data/shadcn_blocks_by_category.json and rebuild navigation caches.",
            },
            {
                "question": "Are animations included?",
                "answer": "We provide sensible defaults. Extend them with data attributes inside the snippets.",
            },
        ],
        "highlight": {
            "label": "Tip",
            "title": "Embed FAQs alongside pricing",
            "copy": "Pair faq-03 with pricing-02 so buyers see benefits and billing in the same scroll.",
        },
    },
    "faq-04": {
        "layout": "split",
        "list": [
            {
                "question": "How quickly can we ship Basecoat clones?",
                "answer": "Teams typically port a block family every sprint once macros and data builders are in place.",
            },
            {
                "question": "Do you sync with shadcn updates?",
                "answer": "Yes—we watch the RSS feed and open PRs when new reference blocks drop.",
            },
        ],
        "sidebar": {
            "title": "Support channels",
            "items": [
                {"label": "Status page", "description": "Track Basecoat releases and planned maintenance windows."},
                {"label": "Component registry", "description": "Browse all cloned variants and dark mode previews."},
                {"label": "CLI onboarding", "description": "Install the CLI to scaffold Basecoat-ready Flask blueprints."},
            ],
        },
        "cta": {"label": "Open support docs", "style": "secondary"},
    },
}


def _merge(data: FaqVariant) -> FaqVariant:
    merged = deepcopy(_FAQ_DEFAULT)
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            merged[key] = deepcopy(value)
        else:
            merged[key] = value
    return merged


def build_faq_variant(name: str) -> FaqVariant:
    blueprint = _FAQ_BLUEPRINTS.get(name)
    if not blueprint:
        raise KeyError(f"Unknown FAQ variant: {name}")
    return _merge(blueprint)


def all_faq_variant_data() -> Dict[str, FaqVariant]:
    return {name: build_faq_variant(name) for name in _FAQ_BLUEPRINTS}
