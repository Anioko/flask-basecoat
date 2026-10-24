"""
Component registry for the gallery and the docs component pages.

A component is registered by adding one module to ``flask_basecoat/gallery_entries/``
named after the component (``button.py``, ``radio_group.py``) that defines an ``ENTRY`` dict.
Nothing else is edited: the gallery routes, the gallery index links and the docs
usage examples are all built from the entries found here.

ENTRY keys (all optional except ``name``):

``name``              Component name as used in docs URLs, e.g. ``'button'``.
``gallery_template``  Template of the component's gallery page, e.g. ``'basecoat/gallery_button.html'``.
                      Served at ``/gallery/<name>`` with endpoint ``gallery_<name>`` (``-`` becomes ``_``).
``themed``            True (default): the page gets ``theme`` ('light' or 'dark') from ``?theme=``.
``index_label``       Link text on the gallery index. Required with ``gallery_template``.
``index_slot``        ``'nav'`` (default, the Components list) or ``'header'`` (button row in the page header).
``order``             Sort position on the index; ties sort by name. Default 1000.
``docs``              Jinja source for the usage examples on the docs component page.
``related``           Component names listed under Related Components on the docs page.
"""
import importlib
import pkgutil
from dataclasses import dataclass
from functools import lru_cache

INDEX_SLOTS = ('nav', 'header')
_KEYS = {'name', 'gallery_template', 'themed', 'index_label', 'index_slot', 'order', 'docs', 'related'}


@dataclass(frozen=True)
class Entry:
    name: str
    gallery_template: str = None
    themed: bool = True
    index_label: str = None
    index_slot: str = 'nav'
    order: int = 1000
    docs: str = None
    related: tuple = ()

    @property
    def endpoint(self):
        return 'gallery_' + self.name.replace('-', '_')


def _build(module_name, data):
    unknown = set(data) - _KEYS
    if unknown:
        raise ValueError(f"gallery entry {module_name}: unknown keys {sorted(unknown)}")
    if 'name' not in data:
        raise ValueError(f"gallery entry {module_name}: missing 'name'")
    if data['name'].replace('-', '_') != module_name:
        raise ValueError(f"gallery entry {module_name}: name {data['name']!r} does not match the file name")
    entry = Entry(**{**data, 'related': tuple(data.get('related', ()))})
    if entry.index_slot not in INDEX_SLOTS:
        raise ValueError(f"gallery entry {module_name}: index_slot must be one of {INDEX_SLOTS}")
    if entry.gallery_template and not entry.index_label:
        raise ValueError(f"gallery entry {module_name}: gallery_template needs index_label")
    return entry


def load_entries(package='flask_basecoat.gallery_entries'):
    """Import every module in the entries package and return its entries sorted by (order, name)."""
    pkg = importlib.import_module(package)
    entries = {}
    for info in pkgutil.iter_modules(pkg.__path__):
        module = importlib.import_module(f'{package}.{info.name}')
        entry = _build(info.name, module.ENTRY)
        entries[entry.name] = entry
    return sorted(entries.values(), key=lambda e: (e.order, e.name))


@lru_cache(maxsize=None)
def get_entries():
    return tuple(load_entries())


def get_entry(name):
    return next((e for e in get_entries() if e.name == name), None)


def gallery_entries(slot=None):
    """Entries that have a gallery page, optionally only those linked from the given index slot."""
    return [e for e in get_entries() if e.gallery_template and (slot is None or e.index_slot == slot)]
