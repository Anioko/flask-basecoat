"""Data builders for call-to-action block variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

CTAData = Dict[str, object]

_CTA_DEFAULT: CTAData = {
    "eyebrow": "Call to action",
    "headline": "Ready to build with Basecoat UI?",
    "description": "Accelerate product delivery with drop-in shadcn/ui blocks tailored for Flask teams.",
    "layout": "centered",
    "actions": [],
}

_CTA_BLUEPRINTS: Dict[str, CTAData] = {
    "cta-01": {
        "layout": "centered",
        "headline": "Launch your next experience in days",
        "description": "Use Basecoat to assemble marketing, onboarding, and product flows backed by consistent tokens.",
        "actions": [
            {"label": "Start free trial", "style": "primary"},
            {"label": "View pricing", "style": "ghost"},
        ],
        "supporting": {
            "label": "Trusted by teams shipping weekly",
            "logos": ["Nebula", "Northwind", "Helio", "Alignly"],
        },
    },
    "cta-02": {
        "layout": "split",
        "eyebrow": "Compose journeys",
        "headline": "Design once, reuse everywhere",
        "description": "Pair Basecoat Studio with shadcn blocks to orchestrate cohesive user journeys across products.",
        "actions": [
            {"label": "Book a walkthrough", "style": "secondary"},
        ],
        "bullets": [
            "Figma and React sources stay in sync",
            "Compliant patterns reviewed by accessibility leads",
            "Analytics instrumentation included out of the box",
        ],
        "media": {
            "caption": "Basecoat Studio workspace",
            "meta": "Live preview updating in realtime",
        },
    },
    "cta-03": {
        "layout": "banner",
        "headline": "Bring Basecoat UI to your platform",
        "description": "Governance-ready foundations that unlock faster launches with measurable quality gains.",
        "actions": [
            {"label": "Talk to our team", "style": "primary"},
        ],
        "metrics": [
            {"label": "faster launches", "value": "+38%"},
            {"label": "accessibility issues", "value": "-72%"},
            {"label": "design/dev review cycles", "value": "2x quicker"},
        ],
    },
    "cta-04": {
        "layout": "inline",
        "headline": "Join the Basecoat release notes",
        "description": "Monthly updates on new block families, migration guides, and product launches.",
        "actions": [
            {"label": "Subscribe", "style": "primary"},
        ],
        "form": {
            "placeholder": "you@company.com",
            "aria_label": "Email address",
            "disclaimer": "No spam. Unsubscribe anytime.",
        },
    },
}


def _merge_cta(data: CTAData) -> CTAData:
    merged = deepcopy(_CTA_DEFAULT)
    for key, value in data.items():
        if isinstance(value, list):
            merged[key] = deepcopy(value)
        elif isinstance(value, dict):
            merged[key] = deepcopy(value)
        else:
            merged[key] = value
    return merged


def build_cta_variant(name: str) -> CTAData:
    blueprint = _CTA_BLUEPRINTS.get(name)
    if not blueprint:
        raise KeyError(f"Unknown CTA variant: {name}")
    return _merge_cta(blueprint)


def all_cta_variant_data() -> Dict[str, CTAData]:
    return {name: build_cta_variant(name) for name in _CTA_BLUEPRINTS}
