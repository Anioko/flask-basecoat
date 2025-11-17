"""Data builders for testimonial block variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

TestimonialData = Dict[str, object]

_TESTIMONIAL_DEFAULT: TestimonialData = {
    "eyebrow": "Testimonials",
    "headline": "Teams ship faster with Basecoat UI",
    "description": "Product leaders share how Basecoat blocks accelerate release cycles.",
    "layout": "grid",
    "quotes": [],
    "meta": "Stories collected from multi-product SaaS teams using Basecoat.",
}

_TESTIMONIAL_BLUEPRINTS: Dict[str, TestimonialData] = {
    "testimonial-01": {
        "layout": "grid",
        "quotes": [
            {
                "quote": "Basecoat's pre-built flows let us redesign onboarding in days instead of months.",
                "author": "Kai Parker",
                "role": "Head of Product Design",
                "company": "Nebula Systems",
                "initials": "KP",
            },
            {
                "quote": "Our designers iterate faster because every block already respects our tokens.",
                "author": "Anya Singh",
                "role": "Design Operations Lead",
                "company": "Atlas Metrics",
                "initials": "AS",
            },
            {
                "quote": "Stakeholders finally see polished prototypes without engineering in the loop.",
                "author": "Milo Chen",
                "role": "Product Manager",
                "company": "Lumen AI",
                "initials": "MC",
            },
        ],
        "cta": {"label": "Explore customer stories", "style": "secondary"},
    },
    "testimonial-02": {
        "layout": "highlight",
        "headline": "Loved by scaling product teams",
        "featured": {
            "quote": "Release velocity nearly doubled after migrating our marketing flows to Basecoat blocks.",
            "author": "Nia Flores",
            "role": "Director of Engineering",
            "company": "Orbit Labs",
            "rating": 4.9,
            "metric": "Launch cadence +42%",
            "initials": "NF",
        },
        "supporting": [
            {
                "quote": "Approvals happen faster because content, design, and dev review the same block preview.",
                "author": "Rowan Patel",
                "role": "Product Marketing",
                "company": "Tandem Cloud",
                "initials": "RP",
            },
            {
                "quote": "Even regulated teams signed off because accessibility is baked into every component.",
                "author": "Inez Castillo",
                "role": "Compliance Lead",
                "company": "Helio Bank",
                "initials": "IC",
            },
        ],
        "cta": {"label": "Read the full case study", "style": "primary"},
        "meta": "Snapshot of Q3 customer sentiment surveys.",
    },
    "testimonial-03": {
        "layout": "logo-wall",
        "logos": [
            {"name": "Planify"},
            {"name": "Northwind"},
            {"name": "Astrolite"},
            {"name": "Optimo"},
            {"name": "Alignly"},
        ],
        "quotes": [
            {
                "quote": "We re-launched six core journeys using Basecoat sections with zero regression bugs.",
                "author": "Jun Kobayashi",
                "role": "VP of Engineering",
                "company": "Planify",
                "initials": "JK",
            },
            {
                "quote": "The content team edits testimonials directly in docs without asking for new mocks.",
                "author": "Lauren Price",
                "role": "Content Strategy",
                "company": "Astrolite",
                "initials": "LP",
            },
        ],
        "meta": "Trusted by growth-stage SaaS teams across three continents.",
    },
    "testimonial-04": {
        "layout": "split",
        "featured": {
            "quote": "We replaced brittle marketing pages with Basecoat layouts that our CMS can reuse instantly.",
            "author": "Morgan Lee",
            "role": "Growth Lead",
            "company": "SharedSignal",
            "badge": "Enterprise rollout",
            "initials": "ML",
        },
        "stats": [
            {"label": "Implementation", "value": "3 weeks"},
            {"label": "Conversion lift", "value": "+28%"},
            {"label": "Support tickets", "value": "-63%"},
        ],
        "secondary": [
            {
                "quote": "Authors can swap testimonial variants without submitting a Jira ticket.",
                "author": "Jamie Fox",
                "role": "Digital Experience Manager",
                "company": "SharedSignal",
                "initials": "JF",
            },
            {
                "quote": "Once we aligned tokens, launching localized pages was a content-only task.",
                "author": "Aria Patel",
                "role": "Localization PM",
                "company": "SharedSignal",
                "initials": "AP",
            },
        ],
        "cta": {"label": "Connect with our team", "style": "ghost"},
        "meta": "Numbers reported after migrating 12 campaign pages.",
    },
}


def _merge_testimonial(data: TestimonialData) -> TestimonialData:
    merged = deepcopy(_TESTIMONIAL_DEFAULT)
    for key, value in data.items():
        if isinstance(value, list):
            merged[key] = deepcopy(value)
        elif isinstance(value, dict):
            merged[key] = deepcopy(value)
        else:
            merged[key] = value
    return merged


def build_testimonial_variant(name: str) -> TestimonialData:
    blueprint = _TESTIMONIAL_BLUEPRINTS.get(name)
    if not blueprint:
        raise KeyError(f"Unknown testimonial variant: {name}")
    return _merge_testimonial(blueprint)


def all_testimonial_variant_data() -> Dict[str, TestimonialData]:
    return {name: build_testimonial_variant(name) for name in _TESTIMONIAL_BLUEPRINTS}
