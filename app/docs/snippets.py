"""Resolve block snippet templates and context for docs previews."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Optional

from app.docs.calendar_data import build_calendar_variant
from app.docs.cta_data import build_cta_variant
from app.docs.drawer_data import build_drawer_variant
from app.docs.faq_data import build_faq_variant
from app.docs.feature_data import build_feature_variant
from app.docs.hero_data import build_hero_variant
from app.docs.pricing_data import build_pricing_variant
from app.docs.testimonial_data import build_testimonial_variant
from app.docs.auth_data import build_auth_variant


@dataclass(frozen=True)
class SnippetSpec:
    template: str
    context: Dict[str, object]


_SIDEBAR_BASE_DATA: Dict[str, object] = {
    "versions": ["1.0.1", "1.1.0-alpha", "2.0.0-beta1"],
    "nav_main": [
        {
            "title": "Getting Started",
            "url": "#",
            "items": [
                {"title": "Installation", "url": "#"},
                {"title": "Project Structure", "url": "#"},
            ],
        },
        {
            "title": "Building Your Application",
            "url": "#",
            "items": [
                {"title": "Routing", "url": "#"},
                {"title": "Data Fetching", "url": "#", "is_active": True},
                {"title": "Rendering", "url": "#"},
                {"title": "Caching", "url": "#"},
                {"title": "Styling", "url": "#"},
                {"title": "Optimizing", "url": "#"},
                {"title": "Configuring", "url": "#"},
                {"title": "Testing", "url": "#"},
                {"title": "Authentication", "url": "#"},
                {"title": "Deploying", "url": "#"},
                {"title": "Upgrading", "url": "#"},
                {"title": "Examples", "url": "#"},
            ],
        },
        {
            "title": "API Reference",
            "url": "#",
            "items": [
                {"title": "Components", "url": "#"},
                {"title": "File Conventions", "url": "#"},
                {"title": "Functions", "url": "#"},
                {"title": "next.config.js Options", "url": "#"},
                {"title": "CLI", "url": "#"},
                {"title": "Edge Runtime", "url": "#"},
            ],
        },
        {
            "title": "Architecture",
            "url": "#",
            "items": [
                {"title": "Accessibility", "url": "#"},
                {"title": "Fast Refresh", "url": "#"},
                {"title": "Next.js Compiler", "url": "#"},
                {"title": "Supported Browsers", "url": "#"},
                {"title": "Turbopack", "url": "#"},
            ],
        },
    ],
    "breadcrumbs": [
        {"label": "Building Your Application", "url": "#"},
        {"label": "Data Fetching"},
    ],
    "cards": [
        {
            "title": "Realtime metrics",
            "copy": "Monitor fetch success rates and latency.",
        },
        {
            "title": "Inline examples",
            "copy": "Preview API patterns before shipping updates.",
        },
        {
            "title": "Change history",
            "copy": "Review documentation diffs at a glance.",
        },
    ],
    "canvas": {
        "title": "Platform delivery timeline",
        "copy": "Upcoming milestones for the Nebula UI documentation platform.",
        "timeline": [
            {"title": "Caching spec", "meta": "Due Friday"},
            {"title": "Streaming guide", "meta": "Review next week"},
            {"title": "Routing API", "meta": "Launch in sprint 24"},
        ],
        "activity": [
            {"label": "Active PRs", "value": "18"},
            {"label": "Open RFCs", "value": "5"},
            {"label": "Content owners", "value": "12"},
        ],
    },
}


def _make_sidebar_data(
    *,
    extra_groups: Optional[list[dict[str, object]]] = None,
    group_defaults: Optional[dict[str, object]] = None,
) -> Dict[str, object]:
    data = deepcopy(_SIDEBAR_BASE_DATA)
    if group_defaults:
        for group in data.get("nav_main", []):
            group.update(group_defaults)
    if extra_groups:
        data.setdefault("nav_main", []).extend(deepcopy(extra_groups))
    return data


_SIDEBAR_02_DATA = _make_sidebar_data(
    extra_groups=[
        {
            "title": "Community",
            "url": "#",
            "items": [
                {"title": "Contribution Guide", "url": "#"},
            ],
            "is_open": True,
        }
    ],
    group_defaults={"is_open": True},
)

_SIDEBAR_02_NAV = _SIDEBAR_02_DATA.get("nav_main", [])
if _SIDEBAR_02_NAV:
    _SIDEBAR_02_NAV[0]["action"] = {"label": "Docs home", "url": "#"}
if len(_SIDEBAR_02_NAV) > 1:
    _SIDEBAR_02_NAV[1]["action"] = {"label": "Roadmap", "url": "#"}
if len(_SIDEBAR_02_NAV) > 2:
    _SIDEBAR_02_NAV[2]["action"] = {"label": "API index", "url": "#"}


_SIDEBAR_VARIANTS: Dict[str, Dict[str, object]] = {
    "sidebar-01": {
        "variant": "basic",
        "features": ["Sectioned navigation", "Primary CTA"],
        "badge": "Default",
        "template": "docs/pages/blocks/snippets/sidebar/sidebar-01.html",
        "data": _make_sidebar_data(),
    },
    "sidebar-02": {
        "variant": "collapsible",
        "features": ["Collapsible groups", "Secondary actions"],
        "badge": "Collapsible",
        "template": "docs/pages/blocks/snippets/sidebar/sidebar-02.html",
        "data": _SIDEBAR_02_DATA,
    },
    "sidebar-03": {"variant": "submenu", "features": ["Fly-out submenu", "Highlighted selection"], "badge": "Nested"},
    "sidebar-04": {"variant": "floating", "features": ["Floating panel", "Shadow elevation"], "badge": "Floating"},
    "sidebar-05": {"variant": "collapsible-submenu", "features": ["Accordion sections", "Compact items"], "badge": "Accordion"},
    "sidebar-06": {"variant": "dropdown", "features": ["Dropdown submenus", "Group labels"], "badge": "Dropdown"},
    "sidebar-07": {"variant": "icon", "features": ["Icon rail", "Condensed layout"], "badge": "Compact"},
    "sidebar-08": {"variant": "inset", "features": ["Inset shell", "Secondary list"], "badge": "Inset"},
    "sidebar-09": {"variant": "nested", "features": ["Two-level tree", "Breadcrumb trail"], "badge": "Nested"},
    "sidebar-10": {"variant": "popover", "features": ["Command palette", "Quick search"], "badge": "Popover"},
    "sidebar-11": {"variant": "files", "features": ["File explorer", "Action toolbar"], "badge": "Files"},
    "sidebar-12": {"variant": "calendar", "features": ["Sidebar calendar", "Upcoming events"], "badge": "Calendar"},
    "sidebar-13": {"variant": "dialog", "features": ["Modal shell", "Multi-column menu"], "badge": "Dialog"},
    "sidebar-14": {"variant": "right", "features": ["Right aligned", "Sticky shortcuts"], "badge": "Right"},
    "sidebar-15": {"variant": "dual", "features": ["Dual rails", "Pinned filters"], "badge": "Dual"},
    "sidebar-16": {"variant": "sticky", "features": ["Sticky header", "Quick actions"], "badge": "Sticky"},
}

_LOGIN_VARIANTS: Dict[str, Dict[str, object]] = {
    "login-01": {"layout": "card", "headline": "Welcome back", "subtitle": "Sign in to continue."},
    "login-02": {"layout": "split", "headline": "Workspace access", "subtitle": "Enter your credentials.", "cover": "city"},
    "login-03": {"layout": "muted", "headline": "Hello again", "subtitle": "Use your email and password."},
    "login-04": {"layout": "media", "headline": "Marketing suite", "subtitle": "Log in to manage campaigns.", "cover": "dashboard"},
    "login-05": {"layout": "email", "headline": "Magic link login", "subtitle": "We will email you a secure link."},
}

_SIGNUP_VARIANTS: Dict[str, Dict[str, object]] = {
    "signup-01": {"layout": "card", "headline": "Create account", "subtitle": "Start building with Basecoat."},
    "signup-02": {"layout": "split", "headline": "Join the workspace", "subtitle": "A few details to get started.", "cover": "gradient"},
    "signup-03": {"layout": "muted", "headline": "Welcome aboard", "subtitle": "Enter your details below."},
    "signup-04": {"layout": "media", "headline": "Marketing suite", "subtitle": "Grow your audience with us.", "cover": "team"},
    "signup-05": {"layout": "social", "headline": "Sign up", "subtitle": "Choose a provider or email."},
}

_OTP_VARIANTS: Dict[str, Dict[str, object]] = {
    "otp-01": {"layout": "card", "headline": "Verify code", "subtitle": "Enter the 6-digit code we sent."},
    "otp-02": {"layout": "split", "headline": "Two factor", "subtitle": "Check your messages for the code.", "cover": "security"},
    "otp-03": {"layout": "muted", "headline": "One-time password", "subtitle": "Secure your login."},
    "otp-04": {"layout": "media", "headline": "Device verification", "subtitle": "Confirm this device to continue.", "cover": "devices"},
    "otp-05": {"layout": "card", "headline": "Verify with provider", "subtitle": "Use SMS or authenticator."},
}

_DASHBOARD_VARIANTS: Dict[str, Dict[str, object]] = {
    "dashboard-01": {
        "headline": "Growth overview",
        "kpis": [
            {"label": "Active users", "value": "18,204", "delta": "+14%"},
            {"label": "MRR", "value": "$124K", "delta": "+6.2%"},
            {"label": "Churn", "value": "1.2%", "delta": "-0.4%"},
        ],
    }
}

_CALENDAR_VARIANTS: Dict[str, Dict[str, object]] = {
    "calendar-01": {
        "mode": "single",
        "label": "Single date",
        "template": "docs/pages/blocks/snippets/calendar/calendar-base.html",
    },
    "calendar-02": {"mode": "single", "label": "Two months", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-03": {"mode": "multi", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-04": {"mode": "range", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-05": {"mode": "range", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-06": {"mode": "range", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-07": {"mode": "range", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-08": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-09": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-10": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-11": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-12": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-13": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-14": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-15": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-16": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-17": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-18": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-19": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-20": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-21": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-22": {"mode": "picker", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-23": {"mode": "range-picker", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-24": {"mode": "picker", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-25": {"mode": "range-picker", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-26": {"mode": "range", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-27": {"mode": "filter", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-28": {"mode": "input", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-29": {"mode": "natural", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-30": {"mode": "single", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-31": {"mode": "events", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
    "calendar-32": {"mode": "drawer", "template": "docs/pages/blocks/snippets/calendar/calendar-base.html"},
}

for _calendar_name, _calendar_variant in _CALENDAR_VARIANTS.items():
    data = build_calendar_variant(_calendar_name)
    _calendar_variant["data"] = data
    _calendar_variant["mode"] = data.get("mode", _calendar_variant.get("mode"))
    _calendar_variant.setdefault("label", data.get("header", {}).get("meta"))
    _calendar_variant["name"] = _calendar_name


_DRAWER_VARIANTS: Dict[str, Dict[str, object]] = {
    "drawer-01": {"template": "docs/pages/blocks/snippets/drawer/drawer-base.html"},
    "drawer-02": {"template": "docs/pages/blocks/snippets/drawer/drawer-base.html"},
    "drawer-03": {"template": "docs/pages/blocks/snippets/drawer/drawer-base.html"},
    "drawer-04": {"template": "docs/pages/blocks/snippets/drawer/drawer-base.html"},
    "drawer-05": {"template": "docs/pages/blocks/snippets/drawer/drawer-base.html"},
}

for _drawer_name, _drawer_variant in _DRAWER_VARIANTS.items():
    data = build_drawer_variant(_drawer_name)
    _drawer_variant["data"] = data
    _drawer_variant.setdefault("label", data.get("label"))
    _drawer_variant["name"] = _drawer_name


_PRICING_VARIANTS: Dict[str, Dict[str, object]] = {
    "pricing-01": {"template": "docs/pages/blocks/snippets/pricing/pricing-base.html"},
    "pricing-02": {"template": "docs/pages/blocks/snippets/pricing/pricing-base.html"},
    "pricing-03": {"template": "docs/pages/blocks/snippets/pricing/pricing-base.html"},
    "pricing-04": {"template": "docs/pages/blocks/snippets/pricing/pricing-base.html"},
}

for _pricing_name, _pricing_variant in _PRICING_VARIANTS.items():
    data = build_pricing_variant(_pricing_name)
    _pricing_variant["data"] = data
    _pricing_variant.setdefault("label", data.get("headline"))
    _pricing_variant["layout"] = data.get("layout")
    _pricing_variant["name"] = _pricing_name


_FAQ_VARIANTS: Dict[str, Dict[str, object]] = {
    "faq-01": {"template": "docs/pages/blocks/snippets/faq/faq-base.html"},
    "faq-02": {"template": "docs/pages/blocks/snippets/faq/faq-base.html"},
    "faq-03": {"template": "docs/pages/blocks/snippets/faq/faq-base.html"},
    "faq-04": {"template": "docs/pages/blocks/snippets/faq/faq-base.html"},
}

for _faq_name, _faq_variant in _FAQ_VARIANTS.items():
    data = build_faq_variant(_faq_name)
    _faq_variant["data"] = data
    _faq_variant.setdefault("label", data.get("headline"))
    _faq_variant["layout"] = data.get("layout")
    _faq_variant["name"] = _faq_name


_FEATURE_VARIANTS: Dict[str, Dict[str, object]] = {
    "feature-01": {"template": "docs/pages/blocks/snippets/feature/feature-base.html"},
    "feature-02": {"template": "docs/pages/blocks/snippets/feature/feature-base.html"},
    "feature-03": {"template": "docs/pages/blocks/snippets/feature/feature-base.html"},
    "feature-04": {"template": "docs/pages/blocks/snippets/feature/feature-base.html"},
}

for _feature_name, _feature_variant in _FEATURE_VARIANTS.items():
    data = build_feature_variant(_feature_name)
    _feature_variant["data"] = data
    _feature_variant.setdefault("label", data.get("headline"))
    _feature_variant["layout"] = data.get("layout")
    _feature_variant["name"] = _feature_name


_CTA_VARIANTS: Dict[str, Dict[str, object]] = {
    "cta-01": {"template": "docs/pages/blocks/snippets/cta/cta-base.html"},
    "cta-02": {"template": "docs/pages/blocks/snippets/cta/cta-base.html"},
    "cta-03": {"template": "docs/pages/blocks/snippets/cta/cta-base.html"},
    "cta-04": {"template": "docs/pages/blocks/snippets/cta/cta-base.html"},
}

for _cta_name, _cta_variant in _CTA_VARIANTS.items():
    data = build_cta_variant(_cta_name)
    _cta_variant["data"] = data
    _cta_variant.setdefault("label", data.get("headline"))
    _cta_variant["layout"] = data.get("layout")
    _cta_variant["name"] = _cta_name


_HERO_VARIANTS: Dict[str, Dict[str, object]] = {
    "hero-01": {"template": "docs/pages/blocks/snippets/hero/hero-base.html"},
    "hero-02": {"template": "docs/pages/blocks/snippets/hero/hero-base.html"},
    "hero-03": {"template": "docs/pages/blocks/snippets/hero/hero-base.html"},
    "hero-04": {"template": "docs/pages/blocks/snippets/hero/hero-base.html"},
}

for _hero_name, _hero_variant in _HERO_VARIANTS.items():
    data = build_hero_variant(_hero_name)
    _hero_variant["data"] = data
    _hero_variant.setdefault("label", data.get("headline"))
    _hero_variant["layout"] = data.get("layout")
    _hero_variant["name"] = _hero_name


_AUTH_VARIANTS: Dict[str, Dict[str, object]] = {
    "login-01": {"template": "docs/pages/blocks/snippets/auth/auth-base.html"},
    "login-02": {"template": "docs/pages/blocks/snippets/auth/auth-base.html"},
    "signup-01": {"template": "docs/pages/blocks/snippets/auth/auth-base.html"},
    "signup-02": {"template": "docs/pages/blocks/snippets/auth/auth-base.html"},
}

for _auth_name, _auth_variant in _AUTH_VARIANTS.items():
    data = build_auth_variant(_auth_name)
    _auth_variant["data"] = data
    _auth_variant.setdefault("label", data.get("title"))
    _auth_variant["layout"] = data.get("layout")
    _auth_variant["name"] = _auth_name


_TESTIMONIAL_VARIANTS: Dict[str, Dict[str, object]] = {
    "testimonial-01": {"template": "docs/pages/blocks/snippets/testimonial/testimonial-base.html"},
    "testimonial-02": {"template": "docs/pages/blocks/snippets/testimonial/testimonial-base.html"},
    "testimonial-03": {"template": "docs/pages/blocks/snippets/testimonial/testimonial-base.html"},
    "testimonial-04": {"template": "docs/pages/blocks/snippets/testimonial/testimonial-base.html"},
}

for _testimonial_name, _testimonial_variant in _TESTIMONIAL_VARIANTS.items():
    data = build_testimonial_variant(_testimonial_name)
    _testimonial_variant["data"] = data
    _testimonial_variant.setdefault("label", data.get("headline"))
    _testimonial_variant["layout"] = data.get("layout")
    _testimonial_variant["name"] = _testimonial_name


def _sidebar_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _SIDEBAR_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/sidebar_variant.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _login_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _LOGIN_VARIANTS.get(block["name"])
    if not variant:
        return None
    return SnippetSpec(
        template="docs/pages/blocks/snippets/login_variant.html",
        context={"variant": variant},
    )


def _signup_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _SIGNUP_VARIANTS.get(block["name"])
    if not variant:
        return None
    return SnippetSpec(
        template="docs/pages/blocks/snippets/signup_variant.html",
        context={"variant": variant},
    )


def _otp_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _OTP_VARIANTS.get(block["name"])
    if not variant:
        return None
    return SnippetSpec(
        template="docs/pages/blocks/snippets/otp_variant.html",
        context={"variant": variant},
    )


def _dashboard_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _DASHBOARD_VARIANTS.get(block["name"])
    if not variant:
        return None
    return SnippetSpec(
        template="docs/pages/blocks/snippets/dashboard_variant.html",
        context={"variant": variant},
    )


def _calendar_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _CALENDAR_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/calendar_variant.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _drawer_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _DRAWER_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/drawer/drawer-base.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _pricing_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _PRICING_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/pricing/pricing-base.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _faq_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _FAQ_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/faq/faq-base.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _feature_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _FEATURE_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/feature/feature-base.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _cta_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _CTA_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/cta/cta-base.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _hero_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _HERO_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/hero/hero-base.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _auth_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _AUTH_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/auth/auth-base.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def _testimonial_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    variant = _TESTIMONIAL_VARIANTS.get(block["name"])
    if not variant:
        return None
    template = variant.get("template", "docs/pages/blocks/snippets/testimonial/testimonial-base.html")
    return SnippetSpec(
        template=template,
        context={"variant": variant},
    )


def resolve_snippet(block: Dict[str, object]) -> Optional[SnippetSpec]:
    name = block["name"]
    if name.startswith("sidebar-"):
        return _sidebar_snippet(block)
    if name.startswith("login-"):
        return _login_snippet(block)
    if name.startswith("signup-"):
        return _signup_snippet(block)
    if name.startswith("otp-"):
        return _otp_snippet(block)
    if name.startswith("calendar-"):
        return _calendar_snippet(block)
    if name.startswith("drawer-"):
        return _drawer_snippet(block)
    if name.startswith("pricing-"):
        return _pricing_snippet(block)
    if name.startswith("faq-"):
        return _faq_snippet(block)
    if name.startswith("feature-"):
        return _feature_snippet(block)
    if name.startswith("cta-"):
        return _cta_snippet(block)
    if name.startswith("hero-"):
        return _hero_snippet(block)
    if name.startswith("login-") or name.startswith("signup-"):
        return _auth_snippet(block)
    if name.startswith("testimonial-"):
        return _testimonial_snippet(block)
    if name.startswith("dashboard-"):
        return _dashboard_snippet(block)
    return None
