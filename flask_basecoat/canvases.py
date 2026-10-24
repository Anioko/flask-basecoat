"""Registry of the strategy canvases and the capability-map views.

One entry per canvas or view: the macro file under ``templates/basecoat/canvas`` (or ``capability_map``), the example
data under ``data/canvases`` (Northwind Logistics), and the example page under ``templates/examples/canvas``. The
examples blueprint, the gallery index, the docs generator and the tests all read this list, so a new canvas is one
entry here plus those three files.
"""
import json
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent
DATA = _HERE / 'data' / 'canvases'

# slug, title, macro name, form (criteria-v3 1.5), the framework's author
CANVASES = [
    ('business-model-canvas', 'Business Model Canvas', 'business_model_canvas', 'C4', 'Osterwalder and Pigneur'),
    ('lean-canvas', 'Lean Canvas', 'lean_canvas', 'C4', 'Ash Maurya'),
    ('value-proposition-canvas', 'Value Proposition Canvas', 'value_proposition_canvas', 'C4', 'Osterwalder and Pigneur'),
    ('swot-analysis', 'SWOT Analysis', 'swot_analysis', 'C2', 'Humphrey'),
    ('pestle-analysis', 'PESTLE Analysis', 'pestle_analysis', 'C2', 'Aguilar'),
    ('porters-five-forces', "Porter's Five Forces", 'porters_five_forces', 'C2', 'Michael Porter'),
    ('ansoff-matrix', 'Ansoff Matrix', 'ansoff_matrix', 'C2', 'Igor Ansoff'),
    ('balanced-scorecard', 'Balanced Scorecard', 'balanced_scorecard', 'C2', 'Kaplan and Norton'),
    ('blue-ocean', 'Blue Ocean Strategy', 'blue_ocean', 'C2', 'Kim and Mauborgne'),
    ('mckinsey-7s', 'McKinsey 7S', 'mckinsey_7s', 'C2', 'Peters and Waterman'),
    ('empathy-map', 'Empathy Map', 'empathy_map', 'C4', 'Dave Gray, XPLANE'),
    ('product-vision-board', 'Product Vision Board', 'product_vision_board', 'C4', 'Roman Pichler'),
    ('okr', 'OKR', 'okr', 'C2', 'Andy Grove and John Doerr'),
    ('wardley-mapping', 'Wardley Map', 'wardley_mapping', 'C1', 'Simon Wardley'),
]

# slug, title, example route name
CAPABILITY = [
    ('capability-map', 'Capability map', 'C2'),
    ('capability-tree', 'Capability tree', 'C2'),
    ('applications-by-capability', 'Applications by capability', 'C2'),
    ('capability-planning', 'Capability planning', 'C2'),
    ('capability-dialogs', 'Capability dialogs', 'B'),
]


def canvases():
    return [dict(slug=s, title=t, macro=m, form=f, author=a, page=f'examples/canvas/{s}.html', macro_file=f'basecoat/canvas/{s}.html')
            for s, t, m, f, a in CANVASES]


def canvas_data(slug):
    """The example data of one canvas (Northwind Logistics)."""
    return json.loads((DATA / f'{slug}.json').read_text(encoding='utf8'))


def available():
    """Canvases whose macro, data and page all exist (a canvas appears as soon as its three files do)."""
    t = _HERE / 'templates'
    return [c for c in canvases() if (t / c['macro_file']).exists() and (DATA / f"{c['slug']}.json").exists() and (t / c['page']).exists()]
