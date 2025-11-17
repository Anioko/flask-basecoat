from types import SimpleNamespace

from flask import abort, redirect, render_template, url_for

from . import docs
from .catalog import (
    blocks_for_category,
    category_metadata,
    find_block,
    list_categories,
    load_blocks_by_category,
)
from .components import COMPONENT_REGISTRY, get_component, list_components
from .navigation import DOCS_NAV, find_page, first_page, previous_and_next
from .snippets import resolve_snippet


def _blocks_context():
    catalog = load_blocks_by_category()
    categories = []
    for category in list_categories():
        categories.append(
            {
                **category,
                "url": url_for("docs.page", slug=f"blocks/{category['id']}")
            }
        )
    total_blocks = sum(len(items) for items in catalog.values())
    return {
        "block_categories": categories,
        "total_block_count": total_blocks,
    }


def _components_context():
    components = []
    for component_name, component_data in COMPONENT_REGISTRY.items():
        components.append({
            "name": component_name,
            "title": component_data["title"],
            "description": component_data["description"],
            "url": url_for("docs.page", slug=f"components/{component_name}"),
            "variant_count": len(component_data.get("variants", {})),
        })
    return {
        "components": components,
        "total_component_count": len(components),
    }


PAGE_CONTEXT_PROVIDERS = {
    "blocks": _blocks_context,
    "components": _components_context,
}


def _resolve_dynamic_page(slug):
    segments = slug.split("/")
    if len(segments) == 2 and segments[0] == "blocks":
        category_id = segments[1]
        metadata = category_metadata(category_id)
        if not metadata:
            return None
        return {
            "title": f"{metadata['title']} Blocks",
            "slug": slug,
            "description": f"All shadcn/ui blocks tagged as {metadata['title']}.",
            "template": "docs/pages/blocks/category.html",
            "section": "Blocks",
        }

    if len(segments) == 3 and segments[0] == "blocks":
        category_id, block_name = segments[1], segments[2]
        metadata = category_metadata(category_id)
        block = find_block(block_name)
        if not metadata or not block:
            return None
        if metadata["id"] not in block.get("categories", []) and block.get("categories"):
            return None
        return {
            "title": block.get("title", block_name.replace("-", " ").title()),
            "slug": slug,
            "description": block.get("description", ""),
            "template": "docs/pages/blocks/block_detail.html",
            "section": "Blocks",
        }

    if len(segments) == 2 and segments[0] == "components":
        component_name = segments[1]
        component_data = get_component(component_name)
        if not component_data:
            return None
        return {
            "title": component_data["title"],
            "slug": slug,
            "description": component_data["description"],
            "template": "docs/pages/components/component_detail.html",
            "section": "Components",
        }

    return None


def _resolve_page(slug):
    page_data = find_page(slug)
    if page_data:
        return page_data, False
    dynamic = _resolve_dynamic_page(slug)
    if dynamic:
        return dynamic, True
    return None, False


def _category_context(category_id):
    metadata = category_metadata(category_id)
    if not metadata:
        return None

    blocks = []
    for block in blocks_for_category(metadata["id"]):
        name = block["name"]
        blocks.append(
            {
                "name": name,
                "title": name.replace("-", " ").title(),
                "description": block.get("description", ""),
                "url": url_for("docs.page", slug=f"blocks/{metadata['id']}/{name}"),
            }
        )

    return {
        "category": metadata,
        "blocks": blocks,
    }


def _block_context(category_id, block_name):
    metadata = category_metadata(category_id)
    block = find_block(block_name)
    if not metadata or not block:
        return None
    if metadata["id"] not in block.get("categories", []) and block.get("categories"):
        return None

    category_links = []
    for category in block.get("categories", []) or [metadata["id"]]:
        category_meta = category_metadata(category)
        if not category_meta:
            continue
        category_links.append(
            {
                "id": category_meta["id"],
                "title": category_meta["title"],
                "url": url_for(
                    "docs.page", slug=f"blocks/{category_meta['id']}"
                ),
                "is_current": category_meta["id"] == metadata["id"],
            }
        )

    snippet_spec = resolve_snippet(block)
    if not snippet_spec:
        return None

    related = []
    for sibling in blocks_for_category(metadata["id"]):
        if sibling["name"] == block_name:
            continue
        related.append(
            {
                "name": sibling["name"],
                "title": sibling["name"].replace("-", " ").title(),
                "url": url_for(
                    "docs.page", slug=f"blocks/{metadata['id']}/{sibling['name']}"
                ),
            }
        )

    return {
        "category": metadata,
        "block": {
            "name": block["name"],
            "title": block.get("title", block["name"].replace("-", " ").title()),
            "description": block.get("description", ""),
            "categories": category_links,
            "snippet_template": snippet_spec.template,
            "snippet_context": snippet_spec.context,
        },
        "related_blocks": related,
    }


def _context_for_slug(slug):
    context_provider = PAGE_CONTEXT_PROVIDERS.get(slug)
    if context_provider:
        return context_provider()

    segments = slug.split("/")
    if not segments:
        return {}

    if len(segments) == 2 and segments[0] == "components":
        component_name = segments[1]
        component_data = get_component(component_name)
        if not component_data:
            return {}
        
        return {
            "component": {
                "name": component_name,
                "title": component_data["title"],
                "description": component_data["description"],
                "docs_url": component_data.get("docs_url"),
                "variants": component_data.get("variants", {}),
            }
        }

    if segments[0] == "blocks":
        if len(segments) == 2:
            context = _category_context(segments[1])
            if context:
                return context
        if len(segments) == 3:
            context = _block_context(segments[1], segments[2])
            if context:
                return context

    return {}


def _breadcrumb(slug):
    segments = slug.split("/")
    crumbs = []
    path_accumulator = []
    for segment in segments:
        path_accumulator.append(segment)
        current_path = "/".join(path_accumulator)
        page_exists, _ = _resolve_page(current_path)
        crumbs.append(
            {
                "label": segment.replace("-", " ").title(),
                "url": url_for("docs.page", slug=current_path)
                if page_exists and current_path != slug
                else None,
                "is_link": bool(page_exists) and current_path != slug,
            }
        )
    return crumbs


@docs.app_context_processor
def inject_docs_navigation():
    return {"docs_nav": DOCS_NAV}


@docs.route("/docs/")
def docs_index():
    page = first_page()
    if not page:
        abort(404)
    return redirect(url_for("docs.page", slug=page["slug"]))


@docs.route("/docs/<path:slug>/")
@docs.route("/docs/<path:slug>")
def page(slug):
    normalized = slug.strip("/")
    page_data, _ = _resolve_page(normalized)
    if not page_data:
        abort(404)

    prev_page, next_page = previous_and_next(normalized)
    breadcrumbs = _breadcrumb(normalized)

    extra_context = _context_for_slug(normalized)

    page_ns = SimpleNamespace(**page_data)
    prev_ns = SimpleNamespace(**prev_page) if prev_page else None
    next_ns = SimpleNamespace(**next_page) if next_page else None

    return render_template(
        page_data["template"],
        page=page_ns,
        breadcrumbs=breadcrumbs,
        prev_page=prev_ns,
        next_page=next_ns,
        **extra_context,
    )
