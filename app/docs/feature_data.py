"""Data builders for feature block variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

FeatureData = Dict[str, object]

_FEATURE_DEFAULT: FeatureData = {
    "eyebrow": "Features",
    "headline": "Everything teams need to move faster",
    "description": "Flask-Basecoat ships production-grade sections that let cross-functional teams ship without tradeoffs.",
    "layout": "grid",
    "features": [],
}

_FEATURE_BLUEPRINTS: Dict[str, FeatureData] = {
    "feature-01": {
        "layout": "grid",
        "features": [
            {
                "title": "Unified tokens",
                "description": "Manage typography, color, and spacing from one source of truth across every block.",
                "icon": "TK",
            },
            {
                "title": "Composable sections",
                "description": "Drop in Flask-Basecoat layouts that already align with shadcn/ui structure and naming.",
                "icon": "CS",
            },
            {
                "title": "Accessibility baked-in",
                "description": "ARIA patterns, focus states, and contrast validations ship with every component.",
                "icon": "A11Y",
                "badge": "WCAG",
            },
            {
                "title": "Performance budgets",
                "description": "Inline critical styles and lazy-load assets so pages stay under performance budgets.",
                "icon": "PF",
            },
            {
                "title": "Audit-ready",
                "description": "Change logs capture every tweak to blocks, keeping compliance teams unblocked.",
                "icon": "QA",
            },
            {
                "title": "Design <> dev sync",
                "description": "Figma kits mirror implementation so designers and engineers stay in lockstep.",
                "icon": "DX",
            },
        ],
        "cta": {"label": "Browse the feature catalog", "style": "primary"},
        "meta": "Catalog highlights from the Flask-Basecoat feature library.",
    },
    "feature-02": {
        "layout": "split",
        "headline": "Composable journeys across products",
        "description": "Connect marketing, onboarding, and in-product surfaces with consistent primitives.",
        "features": [
            {
                "title": "Migration assistant",
                "description": "Transform legacy templates into Flask-Basecoat-ready sections without downtime.",
            },
            {
                "title": "Theme orchestrator",
                "description": "Roll out brand refreshes across every block with automated token diffing.",
            },
            {
                "title": "Live content slots",
                "description": "Swap messages from your CMS while preserving Flask-Basecoat layout integrity.",
            },
        ],
        "media": {
            "title": "Experience Flask-Basecoat Compose",
            "description": "Visual builder that maps product flows to Flask-Basecoat segments in minutes.",
            "items": [
                {"label": "Flows launched", "value": "28"},
                {"label": "Review cycles saved", "value": "3x"},
                {"label": "Regions", "value": "5"},
            ],
            "caption": "Interactive canvas running inside Flask-Basecoat Studio.",
        },
        "cta": {"label": "See Compose in action", "style": "secondary"},
    },
    "feature-03": {
        "layout": "metrics",
        "headline": "Operational excellence out of the box",
        "description": "Flask-Basecoat keeps multi-product orgs aligned with measurable quality gates.",
        "metrics": [
            {"label": "launch velocity", "value": "+42%"},
            {"label": "bug regressions", "value": "-63%"},
            {"label": "review turnaround", "value": "< 24h"},
        ],
        "features": [
            {
                "title": "Release guardrails",
                "description": "Automated checks ensure each block meets accessibility and performance thresholds before merge.",
            },
            {
                "title": "Analytics instrumentation",
                "description": "Pre-wired events flow into your warehouse so product signals stay actionable.",
            },
            {
                "title": "Service blueprinting",
                "description": "Map operational responsibilities directly within blocks to streamline ownership.",
            },
        ],
        "meta": "Metrics reported by Flask-Basecoat customers after six months in production.",
    },
    "feature-04": {
        "layout": "timeline",
        "headline": "From audit to launch in four steps",
        "description": "Reusable playbooks help teams modernise experiences while shipping improvements continuously.",
        "timeline": [
            {
                "title": "Assess",
                "description": "Inventory existing screens and align them to Flask-Basecoat primitives with guided scoring.",
                "note": "Includes token drift analysis across brands.",
            },
            {
                "title": "Assemble",
                "description": "Compose new experiences with Flask-Basecoat sections tailored to your roadmap.",
                "note": "Pair with Compose to preview page states instantly.",
            },
            {
                "title": "Automate",
                "description": "Wire automated QA, analytics, and content workflows directly into the blocks.",
            },
            {
                "title": "Activate",
                "description": "Roll out updates progressively and track customer impact with built-in dashboards.",
                "note": "Playbooks include stakeholder comms templates for each launch stage.",
            },
        ],
        "cta": {"label": "Download the playbook", "style": "ghost"},
        "meta": "Timeline sourced from Flask-Basecoat customer enablement guides.",
    },
}


def _merge_feature(data: FeatureData) -> FeatureData:
    merged = deepcopy(_FEATURE_DEFAULT)
    for key, value in data.items():
        if isinstance(value, list):
            merged[key] = deepcopy(value)
        elif isinstance(value, dict):
            merged[key] = deepcopy(value)
        else:
            merged[key] = value
    return merged


def build_feature_variant(name: str) -> FeatureData:
    blueprint = _FEATURE_BLUEPRINTS.get(name)
    if not blueprint:
        raise KeyError(f"Unknown feature variant: {name}")
    return _merge_feature(blueprint)


def all_feature_variant_data() -> Dict[str, FeatureData]:
    return {name: build_feature_variant(name) for name in _FEATURE_BLUEPRINTS}
