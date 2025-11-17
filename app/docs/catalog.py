"""Helpers for working with the shadcn block registry data."""

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parent / "data"
_BLOCK_SOURCE_PATH = _DATA_DIR / "shadcn_blocks.json"
_CATEGORY_TITLE_OVERRIDES = {
    "faq": "FAQ",
    "cta": "CTA",
}


def _normalized_name(value: str) -> str:
    return value.replace("_", "-")


def _humanize(value: str) -> str:
    return value.replace("-", " ").title()


@lru_cache(maxsize=1)
def _load_raw_blocks() -> List[Dict[str, object]]:
    if not _BLOCK_SOURCE_PATH.exists():
        return []
    with _BLOCK_SOURCE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_blocks_by_category() -> Dict[str, List[Dict[str, str]]]:
    """Return the cached mapping of category -> block definitions."""
    catalog: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for block in _load_raw_blocks():
        categories = block.get("categories", []) or ["uncategorized"]
        for category in categories:
            category_id = _normalized_name(str(category))
            catalog[category_id].append(
                {
                    "name": block.get("name", ""),
                    "description": block.get("description", ""),
                }
            )

    for blocks in catalog.values():
        blocks.sort(key=lambda entry: entry["name"])
    return dict(sorted(catalog.items(), key=lambda item: item[0]))


@lru_cache(maxsize=1)
def _blocks_index() -> Dict[str, Dict[str, object]]:
    index: Dict[str, Dict[str, object]] = {}
    for block in _load_raw_blocks():
        name = str(block.get("name", ""))
        if not name:
            continue
        index[name] = {
            "name": name,
            "description": block.get("description", ""),
            "categories": [_normalized_name(str(category)) for category in block.get("categories", [])],
        }
    return index


def list_categories() -> List[Dict[str, object]]:
    """Return metadata suitable for rendering a category index."""
    catalog = load_blocks_by_category()
    categories = []
    for category, blocks in catalog.items():
        title = _CATEGORY_TITLE_OVERRIDES.get(category, _humanize(category))
        categories.append(
            {
                "id": category,
                "title": title,
                "count": len(blocks),
            }
        )
    return categories


def category_metadata(category_id: str) -> Optional[Dict[str, object]]:
    category_id = _normalized_name(category_id)
    blocks = load_blocks_by_category().get(category_id)
    if not blocks:
        return None
    title = _CATEGORY_TITLE_OVERRIDES.get(category_id, _humanize(category_id))
    return {
        "id": category_id,
        "title": title,
        "count": len(blocks),
    }


def blocks_for_category(category_id: str) -> List[Dict[str, str]]:
    """Return all blocks for the given category identifier."""
    catalog = load_blocks_by_category()
    return catalog.get(_normalized_name(category_id), [])


def find_block(block_name: str) -> Optional[Dict[str, object]]:
    block = _blocks_index().get(block_name)
    if not block:
        return None
    enriched = block.copy()
    enriched["title"] = _humanize(block_name)
    return enriched
