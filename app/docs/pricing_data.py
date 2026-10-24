"""Data builders for pricing block variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

PricingData = Dict[str, object]

_PLAN_FEATURES_CORE = [
    "Unlimited projects",
    "Shared workspaces",
    "Team permissions",
    "Email support",
]

_PLAN_FEATURES_SCALE = _PLAN_FEATURES_CORE + [
    "Advanced analytics",
    "Automations",
    "Integrations",
]

_PLAN_FEATURES_ENTERPRISE = _PLAN_FEATURES_SCALE + [
    "Dedicated CSM",
    "Onboarding sessions",
    "Security reviews",
]

_PRICING_DEFAULT: PricingData = {
    "eyebrow": "Pricing",
    "headline": "Simple pricing for growing product teams",
    "description": "Plans that flex from startups to global organisations with Flask-Basecoat components pre-integrated.",
    "layout": "classic",
    "billing_toggle": {
        "label": "Billing",
        "options": [
            {"label": "Monthly", "value": "monthly"},
            {"label": "Yearly", "value": "yearly", "badge": "Save 15%"},
        ],
        "active": "monthly",
    },
    "plans": [],
    "footnote": "Prices shown in USD. Contact sales for nonprofit discounts.",
}

_PRICING_BLUEPRINTS: Dict[str, PricingData] = {
    "pricing-01": {
        "layout": "classic",
        "plans": [
            {
                "name": "Starter",
                "price": "$19",
                "period": "month",
                "description": "Foundation for individual makers and early launches.",
                "features": _PLAN_FEATURES_CORE,
                "cta": {"label": "Start free trial", "style": "secondary"},
            },
            {
                "name": "Growth",
                "price": "$49",
                "period": "month",
                "description": "Collaboration and automations for scaling teams.",
                "features": _PLAN_FEATURES_SCALE,
                "badge": "Most popular",
                "highlighted": True,
                "cta": {"label": "Choose Growth", "style": "primary"},
            },
            {
                "name": "Scale",
                "price": "$99",
                "period": "month",
                "description": "Enterprise security with custom analytics layers.",
                "features": _PLAN_FEATURES_ENTERPRISE,
                "cta": {"label": "Talk to sales", "style": "ghost"},
            },
        ],
        "addons": [
            {
                "name": "Analytics pack",
                "price": "$199",
                "detail": "Advanced reporting, Tableau export, and data warehouse sync.",
            },
            {
                "name": "Support SLAs",
                "price": "$299",
                "detail": "24/7 phone escalation with incident retrospectives.",
            },
        ],
    },
    "pricing-02": {
        "layout": "toggle",
        "billing_toggle": {
            "label": "Billing",
            "options": [
                {"label": "Monthly", "value": "monthly"},
                {"label": "Yearly", "value": "yearly", "badge": "2 months free"},
            ],
            "active": "yearly",
        },
        "plans": [
            {
                "name": "Launch",
                "price": "$29",
                "period": "month",
                "price_yearly": "$290",
                "description": "Ship faster with Flask-Basecoat starter kits and docs.",
                "features": [
                    "Up to 5 team seats",
                    "Unlimited components",
                    "Community support",
                ],
                "cta": {"label": "Launch now", "style": "ghost"},
            },
            {
                "name": "Scale",
                "price": "$79",
                "period": "month",
                "price_yearly": "$790",
                "description": "Advanced automation and theme packs for complex apps.",
                "features": [
                    "Up to 25 seats",
                    "Custom themes",
                    "Priority support",
                    "Audit logs",
                ],
                "badge": "Best value",
                "highlighted": True,
                "cta": {"label": "Upgrade", "style": "primary"},
            },
            {
                "name": "Enterprise",
                "price": "Custom",
                "period": "",
                "description": "Partner with our team for rollouts across multiple products.",
                "features": [
                    "Unlimited seats",
                    "SAML SSO",
                    "Design reviews",
                    "Dedicated manager",
                ],
                "cta": {"label": "Contact sales", "style": "secondary"},
            },
        ],
        "announcement": {
            "heading": "Have legacy Semantic UI screens?",
            "copy": "We migrate them to modern Flask-Basecoat layouts without downtime.",
            "action": {"label": "Book migration consult", "url": "#"},
        },
    },
    "pricing-03": {
        "layout": "comparison",
        "plans": [
            {"name": "Starter", "price": "$0", "period": "", "badge": "Free"},
            {"name": "Growth", "price": "$35", "period": "month", "highlighted": True},
            {"name": "Scale", "price": "$85", "period": "month"},
        ],
        "feature_matrix": [
            {
                "label": "Projects",
                "tiers": ["3", "Unlimited", "Unlimited"],
            },
            {
                "label": "Custom themes",
                "tiers": [False, True, True],
            },
            {
                "label": "Audit logs",
                "tiers": [False, True, True],
            },
            {
                "label": "Dedicated support",
                "tiers": [False, "Business hours", "24/7"],
            },
            {
                "label": "AI assistant",
                "tiers": [False, False, True],
            },
        ],
        "comparisons": [
            {
                "plan": "Starter",
                "cta": {"label": "Start building", "style": "ghost"},
            },
            {
                "plan": "Growth",
                "cta": {"label": "Choose Growth", "style": "primary"},
            },
            {
                "plan": "Scale",
                "cta": {"label": "Contact sales", "style": "secondary"},
            },
        ],
        "meta": "Compare features across plans to see what fits best.",
    },
    "pricing-04": {
        "layout": "split",
        "plans": [
            {
                "name": "Scale",
                "price": "$129",
                "period": "month",
                "badge": "Teams 25+",
                "description": "Centralised governance, usage analytics, and release workflows.",
                "features": [
                    "Unlimited component tokens",
                    "Release approvals",
                    "Design tokens API",
                    "Compliance exports",
                ],
                "cta": {"label": "Start enterprise trial", "style": "primary"},
                "highlighted": True,
            },
        ],
        "sidebar": {
            "title": "What's included",
            "items": [
                {
                    "label": "Dedicated onboarding",
                    "detail": "Specialists guide your team through Flask-Basecoat setup and rollout.",
                },
                {
                    "label": "Design system migration",
                    "detail": "Audit existing components and migrate to Flask-Basecoat tokens.",
                },
                {
                    "label": "Change management",
                    "detail": "Enablement kits, stakeholder comms, and live workshops.",
                },
            ],
        },
        "faq": [
            {
                "question": "Can we self-host Flask-Basecoat assets?",
                "answer": "Yes. Plans include private npm registry access and deployment guides.",
            },
            {
                "question": "Do you support purchase orders?",
                "answer": "Enterprise agreements support PO-based billing and net 45 terms.",
            },
        ],
    },
}


def _merge_pricing(data: PricingData) -> PricingData:
    merged = deepcopy(_PRICING_DEFAULT)
    for key, value in data.items():
        if isinstance(value, list):
            merged[key] = deepcopy(value)
        elif isinstance(value, dict):
            merged[key] = deepcopy(value)
        else:
            merged[key] = value
    return merged


def build_pricing_variant(name: str) -> PricingData:
    blueprint = _PRICING_BLUEPRINTS.get(name)
    if not blueprint:
        raise KeyError(f"Unknown pricing variant: {name}")
    return _merge_pricing(blueprint)


def all_pricing_variant_data() -> Dict[str, PricingData]:
    return {name: build_pricing_variant(name) for name in _PRICING_BLUEPRINTS}
