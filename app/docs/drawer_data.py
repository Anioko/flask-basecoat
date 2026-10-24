"""Structured data builders for drawer block variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

DrawerData = Dict[str, Any]


_DRAWER_BLUEPRINTS: Dict[str, DrawerData] = {
    "drawer-01": {
        "label": "Project settings",
        "placement": "right",
        "size": "md",
        "header": {
            "eyebrow": "Project",
            "title": "Project settings",
            "description": "Update release metadata and notification rules before shipping.",
            "badge": {"label": "Live", "tone": "success"},
        },
        "body_sections": [
            {
                "kind": "fields",
                "title": "Details",
                "fields": [
                    {"label": "Project name", "value": "Nebula Launch", "type": "text"},
                    {"label": "Owner", "value": "Maya Patel", "type": "text"},
                    {
                        "label": "Visibility",
                        "value": "Workspace",
                        "type": "select",
                        "hint": "Shared with the entire organization.",
                    },
                ],
            },
            {
                "kind": "toggles",
                "title": "Notifications",
                "toggles": [
                    {
                        "label": "Daily summary",
                        "description": "Send updates every weekday at 9:00 AM.",
                        "checked": True,
                    },
                    {
                        "label": "Approvals",
                        "description": "Alert reviewers when requests are waiting.",
                        "checked": True,
                    },
                    {
                        "label": "Deployments",
                        "description": "Only notify when a deployment fails.",
                        "checked": False,
                    },
                ],
            },
        ],
        "footer": {
            "primary": {"label": "Save changes", "tone": "primary"},
            "secondary": {"label": "Cancel"},
            "tertiary": {"label": "Archive project", "tone": "danger"},
        },
    },
    "drawer-02": {
        "label": "Workflow builder",
        "placement": "left",
        "size": "lg",
        "header": {
            "eyebrow": "Automation",
            "title": "New workflow",
            "description": "Compose the triggers and tasks that automate incident response.",
            "meta": "Draft",
        },
        "body_sections": [
            {
                "kind": "list",
                "title": "Trigger",
                "description": "Choose when this workflow should run.",
                "list_items": [
                    {
                        "title": "Code push",
                        "description": "Run when commits reach the main branch.",
                        "meta": "Primary",
                        "active": True,
                    },
                    {
                        "title": "Issue created",
                        "description": "Listen for new high priority bugs reported from support.",
                        "meta": "Optional",
                    },
                    {
                        "title": "Schedule",
                        "description": "Run at a specific cadence for maintenance tasks.",
                        "meta": "Paused",
                    },
                ],
            },
            {
                "kind": "options",
                "title": "Tasks",
                "description": "Select the steps that should run after the trigger fires.",
                "control": "checkbox",
                "options": [
                    {
                        "label": "Run test suite",
                        "description": "Execute the CI pipeline with smoke and regression suites.",
                        "checked": True,
                    },
                    {
                        "label": "Deploy preview",
                        "description": "Create an ephemeral environment for reviewers.",
                        "checked": True,
                    },
                    {
                        "label": "Notify channel",
                        "description": "Send a message to #launchpad with the release summary.",
                        "checked": False,
                    },
                ],
            },
            {
                "kind": "fields",
                "title": "Escalation",
                "fields": [
                    {
                        "label": "Escalate after",
                        "value": "30 minutes",
                        "type": "select",
                    },
                    {
                        "label": "Fallback owner",
                        "value": "ops@nebula.dev",
                        "type": "text",
                    },
                ],
            },
        ],
        "footer": {
            "primary": {"label": "Create workflow", "tone": "primary"},
            "secondary": {"label": "Cancel"},
        },
    },
    "drawer-03": {
        "label": "Team profile",
        "placement": "right",
        "size": "sm",
        "header": {
            "avatar": {"initials": "AM", "tone": "indigo"},
            "title": "Amelia Moore",
            "description": "Staff product designer — availability 9:00 AM – 5:00 PM PT.",
            "meta": "Design systems",
        },
        "body_sections": [
            {
                "kind": "summary",
                "title": "Contact",
                "summary_items": [
                    {"label": "Email", "value": "amelia@nebula.dev"},
                    {"label": "Location", "value": "Portland, USA"},
                    {"label": "Status", "value": "In office", "badge_tone": "success"},
                ],
            },
            {
                "kind": "timeline",
                "title": "Recent activity",
                "timeline": [
                    {
                        "title": "Reviewed sidebar spec",
                        "time": "2h ago",
                        "description": "Approved layout adjustments for the floating rail.",
                    },
                    {
                        "title": "Joined calendar sync",
                        "time": "Yesterday",
                        "description": "Shared feedback on keyboard interactions.",
                    },
                    {
                        "title": "Shipped Flask-Basecoat theme",
                        "time": "Monday",
                        "description": "Rolled out design tokens v2 to production.",
                    },
                ],
            },
        ],
        "footer": {
            "primary": {"label": "Schedule chat", "tone": "primary"},
            "secondary": {"label": "Message"},
        },
    },
    "drawer-04": {
        "label": "Analytics filters",
        "placement": "right",
        "size": "md",
        "header": {
            "eyebrow": "Filters",
            "title": "Refine analytics",
            "description": "Adjust segments and timeframes to focus the dataset.",
        },
        "body_sections": [
            {
                "kind": "pills",
                "title": "Segments",
                "pills": [
                    {"label": "Active customers", "selected": True},
                    {"label": "Trials", "selected": True},
                    {"label": "Churned"},
                    {"label": "Enterprise"},
                ],
                "add_label": "Add segment",
            },
            {
                "kind": "options",
                "title": "Time range",
                "control": "radio",
                "options": [
                    {
                        "label": "Last 7 days",
                        "description": "Fast-moving indicator",
                        "value": "7d",
                    },
                    {
                        "label": "Last 30 days",
                        "description": "Monthly view",
                        "value": "30d",
                        "checked": True,
                    },
                    {
                        "label": "Quarter to date",
                        "description": "Strategic lens",
                        "value": "qtd",
                    },
                ],
            },
            {
                "kind": "fields",
                "title": "Advanced",
                "fields": [
                    {
                        "label": "Attribution model",
                        "value": "Data-driven",
                        "type": "select",
                    },
                    {
                        "label": "Conversion window",
                        "value": "14 days",
                        "type": "select",
                    },
                ],
            },
        ],
        "footer": {
            "primary": {"label": "Apply filters", "tone": "primary"},
            "secondary": {"label": "Save preset"},
            "tertiary": {"label": "Clear all"},
        },
    },
    "drawer-05": {
        "label": "Release review",
        "placement": "bottom",
        "size": "xl",
        "header": {
            "eyebrow": "Release 2025.11",
            "title": "Review staged release",
            "description": "Confirm the scope before submitting to compliance.",
        },
        "body_sections": [
            {
                "kind": "list",
                "title": "Highlights",
                "list_items": [
                    {
                        "title": "New audit trail",
                        "description": "Capture a full history for high-risk actions.",
                        "meta": "Feature",
                    },
                    {
                        "title": "Latency improvements",
                        "description": "Query times are down 41% in staging.",
                        "meta": "Performance",
                    },
                    {
                        "title": "Resolved incidents",
                        "description": "Cleared all pager alerts tied to this release train.",
                        "meta": "Quality",
                    },
                ],
            },
            {
                "kind": "summary",
                "title": "Checklist",
                "summary_items": [
                    {"label": "Approvals", "value": "Product, Legal"},
                    {
                        "label": "Launch window",
                        "value": "Nov 20, 2025 · 09:00 PT",
                    },
                    {"label": "Risk", "value": "Low", "badge_tone": "success"},
                ],
            },
        ],
        "footer": {
            "primary": {"label": "Submit for review", "tone": "primary"},
            "secondary": {"label": "Share update"},
            "tertiary": {"label": "Dismiss"},
        },
    },
}


def _with_defaults(name: str, blueprint: DrawerData) -> DrawerData:
    data = deepcopy(blueprint)
    data.setdefault("name", name)
    data.setdefault("placement", "right")
    data.setdefault("size", "md")
    data.setdefault("body_sections", [])
    data.setdefault("footer", {})
    data.setdefault("backdrop", True)
    data.setdefault("label", data.get("header", {}).get("title", "Drawer"))
    return data


def build_drawer_variant(name: str) -> DrawerData:
    blueprint = _DRAWER_BLUEPRINTS.get(name)
    if not blueprint:
        return {
            "name": name,
            "label": "Drawer preview",
            "placement": "right",
            "size": "md",
            "header": {
                "title": "Drawer preview",
                "description": "Placeholder for a drawer variant that has not been implemented yet.",
            },
            "body_sections": [],
            "footer": {},
            "backdrop": True,
        }
    return _with_defaults(name, blueprint)


def all_drawer_variant_data() -> Dict[str, DrawerData]:
    return {name: build_drawer_variant(name) for name in _DRAWER_BLUEPRINTS}
