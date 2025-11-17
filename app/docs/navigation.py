DOCS_NAV = [
    {
        "title": "Getting Started",
        "pages": [
            {
                "title": "Introduction",
                "slug": "introduction",
                "description": "Understand the goals of the Basecoat Design System and how it maps to shadcn/ui.",
                "template": "docs/pages/introduction.html"
            },
            {
                "title": "Installation",
                "slug": "installation",
                "description": "Add the Basecoat docs stack to an existing Flask project.",
                "template": "docs/pages/installation.html"
            },
            {
                "title": "Project Structure",
                "slug": "project-structure",
                "description": "How the documentation blueprint and assets are organized.",
                "template": "docs/pages/project_structure.html"
            }
        ]
    },
    {
        "title": "Foundations",
        "pages": [
            {
                "title": "Theming",
                "slug": "theming",
                "description": "Customize colors, typography, and spacing using Basecoat tokens.",
                "template": "docs/pages/theming.html"
            }
        ]
    },
    {
        "title": "Blocks",
        "pages": [
            {
                "title": "Blocks Overview",
                "slug": "blocks",
                "description": "Browse every shadcn block category and Basecoat coverage status.",
                "template": "docs/pages/blocks/index.html"
            },
            {
                "title": "Sidebar Layout",
                "slug": "blocks/sidebar-demo",
                "description": "Replica of the shadcn sidebar block composed with Basecoat UI.",
                "template": "docs/pages/blocks/sidebar.html"
            }
        ]
    },
    {
        "title": "Components",
        "pages": [
            {
                "title": "Components Overview",
                "slug": "components",
                "description": "Browse shadcn/ui components adapted for Flask-Basecoat.",
                "template": "docs/pages/components/index.html"
            },
            {
                "title": "Test Page",
                "slug": "components/test",
                "description": "Test if routing and JSON loading works.",
                "template": "docs/pages/components/test.html"
            },
            {
                "title": "Kanban Board",
                "slug": "components/kanban",
                "description": "Drag-and-drop task board with column organization and status tracking.",
                "template": "docs/pages/components/kanban.html"
            },
            {
                "title": "Task List",
                "slug": "components/list",
                "description": "Interactive task list with drag-and-drop reordering and status management.",
                "template": "docs/pages/components/list.html"
            },
            {
                "title": "Gantt Chart",
                "slug": "components/gantt",
                "description": "Project timeline visualization with task dependencies and milestones.",
                "template": "docs/pages/components/gantt.html"
            }
        ]
    }
]
def _enrich_item(section_title, item):
    enriched = item.copy()
    enriched["section"] = section_title
    return enriched


def iter_pages():
    """Yield every nav item in display order with section metadata."""
    for section in DOCS_NAV:
        for item in section["pages"]:
            yield _enrich_item(section["title"], item)


def _all_pages():
    return list(iter_pages())


def find_page(slug):
    """Return the nav item dict for the given slug."""
    normalized = slug.strip("/")
    for item in _all_pages():
        if item["slug"] == normalized:
            return item
    return None


def previous_and_next(slug):
    """Return the previous and next items relative to slug."""
    pages = _all_pages()
    for index, item in enumerate(pages):
        if item["slug"] == slug:
            prev_item = pages[index - 1] if index > 0 else None
            next_item = pages[index + 1] if index < len(pages) - 1 else None
            return prev_item, next_item
    return None, None


def first_page():
    pages = _all_pages()
    return pages[0] if pages else None
