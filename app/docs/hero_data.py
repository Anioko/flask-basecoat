"""Data builders for hero block variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

HeroData = Dict[str, object]

_HERO_DEFAULT: HeroData = {
    "eyebrow": "Introducing",
    "headline": "Build faster with Flask-Basecoat",
    "description": "Production-grade shadcn/ui blocks that accelerate product delivery for Flask teams.",
    "layout": "centered",
    "actions": [],
}

_HERO_BLUEPRINTS: Dict[str, HeroData] = {
    "hero-01": {
        "layout": "centered",
        "headline": "Ship product journeys in days, not months",
        "description": "Pre-built shadcn/ui blocks with Flask-Basecoat styling eliminate the design-to-development handoff for Flask teams.",
        "actions": [
            {"label": "Browse blocks", "style": "primary"},
            {"label": "View documentation", "style": "secondary"},
        ],
        "highlights": [
            "50+ production-ready blocks",
            "Figma-to-React fidelity",
            "Accessibility audited patterns",
        ],
        "social_proof": {
            "label": "Trusted by product teams",
            "avatars": ["KP", "AS", "MC", "NF", "RP"],
            "count": "250+ teams",
        },
    },
    "hero-02": {
        "layout": "split",
        "eyebrow": "Flask-Basecoat Design System",
        "headline": "Compose experiences that scale",
        "description": "Unify marketing, onboarding, and in-product flows with consistent tokens and validated patterns.",
        "actions": [
            {"label": "Start building", "style": "primary"},
        ],
        "media": {
            "title": "Live component preview",
            "caption": "Every block ships with light and dark theme support",
            "demo_text": "Interactive layouts updating in realtime",
        },
        "stats": [
            {"label": "Components", "value": "120+"},
            {"label": "Themes", "value": "6"},
            {"label": "Accessibility score", "value": "AAA"},
        ],
    },
    "hero-03": {
        "layout": "minimal",
        "headline": "The design system for ambitious Flask projects",
        "description": "Battle-tested blocks that help cross-functional teams ship cohesive experiences faster.",
        "actions": [
            {"label": "Explore the catalog", "style": "primary"},
            {"label": "Read the guide", "style": "ghost"},
        ],
        "announcement": {
            "label": "New release",
            "text": "Pricing and testimonial blocks now available",
            "url": "#",
        },
    },
    "hero-04": {
        "layout": "gradient",
        "eyebrow": "Powered by shadcn/ui",
        "headline": "Enterprise-grade blocks for modern Flask apps",
        "description": "Governance-ready components with built-in analytics, performance monitoring, and compliance patterns.",
        "actions": [
            {"label": "Book enterprise demo", "style": "secondary"},
            {"label": "View enterprise features", "style": "ghost"},
        ],
        "badges": [
            "SOC 2 compliant",
            "WCAG AAA certified",
            "99.9% uptime SLA",
        ],
        "enterprise": {
            "title": "Enterprise features",
            "items": [
                "Private npm registry",
                "24/7 priority support",
                "Custom design tokens",
                "Audit logging",
            ],
        },
    },
}


def _merge_hero(data: HeroData) -> HeroData:
    merged = deepcopy(_HERO_DEFAULT)
    for key, value in data.items():
        if isinstance(value, list):
            merged[key] = deepcopy(value)
        elif isinstance(value, dict):
            merged[key] = deepcopy(value)
        else:
            merged[key] = value
    return merged


def build_hero_variant(name: str) -> HeroData:
    blueprint = _HERO_BLUEPRINTS.get(name)
    if not blueprint:
        raise KeyError(f"Unknown hero variant: {name}")
    return _merge_hero(blueprint)


def all_hero_variant_data() -> Dict[str, HeroData]:
    return {name: build_hero_variant(name) for name in _HERO_BLUEPRINTS}