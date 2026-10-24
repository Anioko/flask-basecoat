"""The page check's gates (A2, A5, B9, R9, Tier C forms, help text): each passes the original it is measured against and
fails a deliberately broken fixture."""
import copy
import importlib.util
import pathlib

import pytest
from lxml import html as lxml_html

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_page', ROOT / 'compliance' / 'scripts' / 'check_page.py')
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)
pg = cp.page_gates
LIMITS = {'regions': 6, 'stat_cards': 4, 'charts': 2, 'tables': 1}


def doc(body, head=''):
    return lxml_html.fromstring(f'<!doctype html><html lang="en"><head>{head}</head><body>{body}</body></html>')


def block(name='dashboard-01'):
    text, _ = cp.load(f'/basecoat/blocks/{name}')
    return lxml_html.fromstring(text)


def original(name='dashboard-01'):
    return lxml_html.fromstring(cp.golden_path(name).read_text(encoding='utf8'))


# ---------------------------------------------------------------- A2 structure

def test_a2_original_matches_at_100_percent():
    fails, r = pg.check_structure(block(), original(), cp.content_roots, tier='A')
    assert fails == [] and r['percent'] == 100.0 and r['frame_percent'] == 100.0


def test_a2_repeated_rows_cards_and_items_collapse_to_one():
    d = block()
    rows = d.xpath('//*[@data-slot="table-body"]/*[@data-slot="table-row"]')
    for _ in range(5):
        rows[0].addnext(copy.deepcopy(rows[0]))
    cards = d.xpath('//*[@data-slot="card"][ancestor::*[@data-slot="sidebar-inset"]]')[0]
    cards.addnext(copy.deepcopy(cards))
    items = d.xpath('//*[@data-slot="sidebar-menu-item"]')[0]
    items.addnext(copy.deepcopy(items))
    fails, r = pg.check_structure(d, original(), cp.content_roots, tier='A')
    assert fails == [] and r['percent'] == 100.0


def test_a2_reports_percent_and_first_differing_node():
    d = block()
    card = d.xpath('//*[@data-slot="card"][ancestor::*[@data-slot="sidebar-inset"]]')[0]
    wrapper = lxml_html.fromstring('<section></section>')
    card.addprevious(wrapper)
    wrapper.append(card)
    fails, r = pg.check_structure(d, original(), cp.content_roots, tier='A')
    assert r['percent'] < 100
    assert fails and 'first differing node' in fails[0]
    assert r['first_difference']['page'] == 'section'
    assert 'sidebar-inset' in r['first_difference']['page_path']


def test_a2_tier_b_needs_the_frame_not_the_whole_page():
    d = block()
    d.xpath('//*[@data-slot="sidebar-inset"]')[0].append(lxml_html.fromstring('<div data-slot="card"></div>'))
    fails, r = pg.check_structure(d, original(), cp.content_roots, tier='B')
    assert fails == [] and r['percent'] < 100          # content differs, frame is the original's
    d.xpath('//*[@data-slot="sidebar-footer"]')[0].getparent().remove(d.xpath('//*[@data-slot="sidebar-footer"]')[0])
    fails, _ = pg.check_structure(d, original(), cp.content_roots, tier='B')
    assert fails and 'frame' in fails[0]


def test_a2_needs_an_original():
    fails, _ = pg.check_structure(block(), None, cp.content_roots)
    assert fails


# ---------------------------------------------------------------- A5 / R9 in the browser

pw = pytest.importorskip('playwright.sync_api')
AXE = ROOT / 'compliance' / 'golden' / 'node_modules' / 'axe-core' / 'axe.min.js'


def served_page(tmp_path, old=None, new=None, name='dashboard-01'):
    text, _ = cp.load(f'/basecoat/blocks/{name}')
    if old:
        assert old in text, old
        text = text.replace(old, new, 1)
    f = tmp_path / 'page.html'
    f.write_text(text, encoding='utf8')
    return str(f), text


def pixels(target, text, tier='A'):
    with pg.page_urls(target, text, 'dashboard-01', 'blocks/dashboard-01.html') as (url, gold):
        return pg.check_pixels(url, gold, tier)


def test_a5_the_original_passes_masked(tmp_path):
    target, text = served_page(tmp_path)
    fails, info = pixels(target, text)
    assert fails == [], info
    assert set(info) == {'light 1440', 'light 390', 'dark 1440', 'dark 390'}


def test_a5_data_changes_are_masked_a_layout_change_is_not(tmp_path):
    target, text = served_page(tmp_path, 'Documents', 'Dossiers')   # same-length text is data: masked
    fails, _ = pixels(target, text)
    assert fails == []
    target, text = served_page(tmp_path, '<main', '<div class="h-24 border bg-primary"></div><main')
    fails, info = pixels(target, text)
    assert fails and 'differ from the golden render' in fails[0], info


def test_png_diff_counts_missing_area():
    import io
    from PIL import Image

    def png(w, h, c):
        b = io.BytesIO()
        Image.new('RGB', (w, h), c).save(b, 'PNG')
        return b.getvalue()
    assert pg.png_diff(png(10, 10, 'white'), png(10, 10, 'white')) == 0
    assert pg.png_diff(png(10, 10, 'white'), png(10, 20, 'white')) == 50.0


def finding(i, impact, n=1):
    return {'id': i, 'impact': impact, 'help': i, 'count': n, 'nodes': ['x']}


def test_r9_serious_and_critical_fail_even_when_the_original_has_them():
    ours = [finding('color-contrast', 'serious'), finding('button-name', 'critical')]
    assert len(pg.judge_a11y(ours, ours, [])) == 2


def test_r9_a_recorded_departure_clears_a_serious_finding():
    ours = [finding('color-contrast', 'serious')]
    dep = [{'check': 'R9', 'rule': 'color-contrast', 'wcag': '1.4.3', 'reason': 'avatar fallback darkened'}]
    assert pg.judge_a11y(ours, ours, dep) == []
    other = [{'check': 'R9', 'rule': 'image-alt', 'wcag': '1.1.1', 'reason': 'x'}]
    assert pg.judge_a11y(ours, ours, other)


def test_r9_a_departure_needs_rule_criterion_and_reason():
    d = doc('', '<meta name="shadcn-departure" content="R9 color-contrast wcag=1.4.3 reason=darker fallback">'
                '<meta name="shadcn-departure" content="R9 image-alt">')
    assert [x['rule'] for x in pg.load_departures(d)] == ['color-contrast']


def test_r9_moderate_and_minor_fail_only_beyond_the_original():
    assert pg.judge_a11y([finding('heading-order', 'moderate', 2)], [finding('heading-order', 'moderate', 2)], []) == []
    assert pg.judge_a11y([finding('heading-order', 'moderate', 3)], [finding('heading-order', 'moderate', 2)], [])
    assert pg.judge_a11y([finding('heading-order', 'minor', 1)], [], [])


@pytest.mark.skipif(not AXE.exists(), reason='axe-core is installed by `npm ci` in compliance/golden')
def test_r9_browser_scan_fails_an_unnamed_image_and_passes_with_a_departure(tmp_path):
    page = tmp_path / 'p.html'
    page.write_text('<!doctype html><html lang="en"><head><title>t</title></head><body><main><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw="></main></body></html>')
    with pg.page_urls(str(page), page.read_text(), None, None) as (url, _):
        fails, _ = pg.check_a11y_strict(url, None, [])
        assert any('image-alt (critical)' in f for f in fails)
        ok, info = pg.check_a11y_strict(url, None, [{'check': 'R9', 'rule': 'image-alt', 'wcag': '1.1.1', 'reason': 'decorative'}])
        assert ok == [] and info['departures']


# ---------------------------------------------------------------- B9 charts

def _render_chart(s, page=False):
    from flask_basecoat.testing import make_app
    app = make_app()
    src = "{% import 'basecoat/index.html' as ui %}{{ ui.chart_from_spec(s, id='x', class='aspect-auto h-[250px] w-full') }}"
    if page:
        src = ("{% extends 'basecoat/pages/_layout.html' %}{% import 'basecoat/index.html' as ui %}{% block body %}<div class=\"w-[600px]\">"
               "{{ ui.chart_from_spec(s, id='x', class='aspect-auto h-[250px] w-full') }}</div>{% endblock %}")
    from flask import render_template_string
    with app.test_request_context():
        return render_template_string(src, s=s)


def b9(mutate=None, name='chart-bar-default'):
    from flask_basecoat.charts import load_spec
    s = load_spec(name)
    if mutate:
        mutate(s)
    return pg.check_charts_static(lxml_html.fromstring(_render_chart(s)))[0]


def test_b9_a_pinned_chart_passes():
    for name in ('chart-bar-default', 'chart-area-interactive', 'chart-pie-donut-text', 'chart-radar-multiple', 'chart-line-multiple'):
        assert b9(name=name) == [], name


def test_b9_the_spec_must_name_a_pinned_chart():
    assert any('names no pinned chart id' in f for f in b9(lambda s: s.pop('chart')))
    assert any('not a pinned chart id' in f for f in b9(lambda s: s.update(chart='chart-nonsense')))


def test_b9_a_different_family_fails():
    assert any('family' in f for f in b9(lambda s: s.update(component='LineChart')))
    assert any('family' in f for f in b9(lambda s: s['series'][0].update(component='Line')))


def test_b9_more_series_than_the_original_fails():
    def more(s):
        s['series'].append(copy.deepcopy(s['series'][0]))
    assert any('series; chart-bar-default has 1' in f for f in b9(more))

    def six(s):
        s['series'] = [copy.deepcopy(s['series'][0]) for _ in range(6)]
    assert any('at most 5' in f for f in b9(six, name='chart-line-multiple'))


def test_b9_colours_are_chart_tokens_only():
    assert any('var(--primary)' in f for f in b9(lambda s: s['config']['desktop'].update(color='var(--primary)')))
    assert any('var(--secondary)' in f for f in b9(lambda s: s['series'][0].update(fill='var(--secondary)')))
    assert any('raw colour' in f for f in b9(lambda s: s['config']['desktop'].update(color='#ff0000')))
    assert any('raw colour' in f for f in b9(lambda s: s['config']['desktop'].update(color='oklch(0.5 0.2 30)')))
    assert b9(lambda s: s['config']['desktop'].update(color='var(--chart-3)')) == []
    assert b9(lambda s: s['config']['desktop'].update(color='var(--muted-foreground)')) == []


def test_b9_the_rendered_chart_is_drawn_in_the_browser(tmp_path):
    from flask_basecoat.charts import load_spec
    f = tmp_path / 'c.html'
    f.write_text(_render_chart(load_spec('chart-bar-default'), page=True))
    with pg.page_urls(str(f), f.read_text(), None, None) as (url, _):
        assert pg.check_charts_rendered(url) == []


# ---------------------------------------------------------------- Tier C forms

def forms(body, head=''):
    return pg.check_forms(doc(body, head))[0]


def has(lines, text):
    return any(text in l for l in lines)


SCROLL = '<div class="overflow-x-auto" role="region" tabindex="0" aria-label="{} scroll horizontally">{}</div>'

# ---- C4 canvas

BMC = {'Key Partners': 'col-start-1 col-span-2 row-start-1 row-span-2', 'Key Activities': 'col-start-3 col-span-2 row-start-1',
       'Key Resources': 'col-start-3 col-span-2 row-start-2', 'Value Propositions': 'col-start-5 col-span-2 row-start-1 row-span-2',
       'Customer Relationships': 'col-start-7 col-span-2 row-start-1', 'Channels': 'col-start-7 col-span-2 row-start-2',
       'Customer Segments': 'col-start-9 col-span-2 row-start-1 row-span-2', 'Cost Structure': 'col-start-1 col-span-5 row-start-3',
       'Revenue Streams': 'col-start-6 col-span-5 row-start-3'}


def canvas(boxes=None, cols='grid-cols-10'):
    boxes = BMC if boxes is None else boxes
    cards = ''.join(f'<div data-slot="card" class="{cls}"><div data-slot="card-header"><div data-slot="card-title">{t}</div></div></div>' for t, cls in boxes.items())
    return f'<div data-entelim-form="c4">' + SCROLL.format('Canvas,', f'<div class="grid {cols}">{cards}</div>') + '</div>'


def test_c4_the_published_business_model_canvas_passes():
    assert forms(canvas()) == []


def test_c4_the_nine_boxes_are_exactly_the_published_ones():
    boxes = dict(BMC)
    boxes['Key Partnerships'] = boxes.pop('Key Partners')            # the wrong wording
    out = forms(canvas(boxes))
    assert has(out, '"Key Partners" is missing') and has(out, '"Key Partnerships" is not one of')
    boxes = dict(BMC)
    del boxes['Channels']
    assert has(forms(canvas(boxes)), '8 boxes')
    assert has(forms(canvas({**BMC, 'Extra': 'col-start-1 col-span-1 row-start-4'})), '10 boxes')


def test_c4_the_arrangement_is_the_published_one():
    swapped = {**BMC, 'Key Activities': BMC['Key Resources'], 'Key Resources': BMC['Key Activities']}
    assert has(forms(canvas(swapped)), 'Key Activities must sit above Key Resources')
    narrow = {**BMC, 'Value Propositions': 'col-start-5 col-span-1 row-start-1 row-span-2'}
    assert has(forms(canvas(narrow)), 'Value Propositions')
    short = {**BMC, 'Customer Segments': 'col-start-9 col-span-2 row-start-1'}
    assert has(forms(canvas(short)), 'full height')
    unequal = {**BMC, 'Cost Structure': 'col-start-1 col-span-6 row-start-3', 'Revenue Streams': 'col-start-7 col-span-4 row-start-3'}
    assert has(forms(canvas(unequal)), 'Cost Structure')
    on_top = {**BMC, 'Cost Structure': 'col-start-1 col-span-5 row-start-1'}
    assert has(forms(canvas(on_top)), 'strip below')


def test_c4_five_columns_cannot_split_the_money_strip_in_half():
    five = {t: c.replace('col-span-2', 'col-span-1').replace('col-span-5', 'col-span-3') for t, c in BMC.items()}
    five = {t: re_col(c) for t, c in five.items()}
    out = forms(canvas(five, 'grid-cols-5'))
    assert has(out, 'Cost Structure') or has(out, 'Revenue Streams')


def re_col(c):
    import re
    return re.sub(r'col-start-(\d+)', lambda m: f'col-start-{(int(m.group(1)) + 1) // 2}', c)


def test_c4_boxes_are_placed_and_the_region_scrolls():
    stacked = {t: '' for t in BMC}
    assert has(forms(canvas(stacked)), 'no col-start')
    no_scroll = canvas().replace('overflow-x-auto', 'overflow-hidden')
    assert has(forms(no_scroll), 'overflow-x-auto')
    unnamed = canvas().replace(' aria-label="Canvas, scroll horizontally"', '')
    assert has(forms(unnamed), 'role="region" with a name')


def test_c4_inline_style_other_than_geometry_is_refused():
    out = forms(canvas().replace('<div data-slot="card" class="col-start-1', '<div style="width:300px" data-slot="card" class="col-start-1', 1))
    assert has(out, "inline style property ['width']")
    assert forms(canvas().replace('<div data-slot="card" class="col-start-1', '<div style="--col:1;--row:1" data-slot="card" class="col-start-1', 1)) == []


# ---- C2 heat map

def heat(rows=None, caption='<caption>Maturity by capability</caption>', extra=''):
    rows = rows or [('Billing', ['3', '4']), ('Orders', ['2', '5'])]
    body = ''.join(f'<tr><th scope="row">{n}</th>' + ''.join(f'<td class="bg-chart-1/{20 * int(v)}">{v}</td>' if v.isdigit() else f'<td>{v}</td>' for v in vs) + '</tr>' for n, vs in rows)
    return (f'<div data-entelim-form="c2">' + SCROLL.format('Heat map,', f'<table data-slot="table">{caption}<thead><tr><th>Capability</th><th>Now</th><th>Target</th></tr></thead><tbody>{body}</tbody></table>') + extra + '</div>')


def test_c2_a_named_table_with_a_value_in_every_cell_passes():
    assert forms(heat()) == []


def test_c2_needs_a_real_table_alternative():
    no_table = '<div data-entelim-form="c2">' + SCROLL.format('Heat map,', '<div class="grid grid-cols-3"><div class="bg-chart-1/40">3</div></div>') + '</div>'
    assert has(forms(no_table), 'no real table alternative')
    assert has(forms(heat(caption='')), 'no real table alternative')


def test_c2_every_cell_carries_a_text_value():
    assert has(forms(heat(rows=[('Billing', ['3', '']), ('Orders', ['2', '5'])])), 'cell carries no text value')
    assert has(forms(heat(rows=[('Billing', ['3', '—']), ('Orders', ['2', '5'])])), 'cell carries no text value')
    assert has(forms(heat(rows=[('Billing', ['3', 'N/A']), ('Orders', ['2', '5'])])), 'cell carries no text value')


def test_c2_rows_are_rectangular_and_steps_are_five_at_most():
    assert has(forms(heat(rows=[('Billing', ['3', '4']), ('Orders', ['2'])])), 'not rectangular')
    many = [('A', ['1', '2', '3']), ('B', ['4', '5', '6'])]
    assert has(forms(heat(rows=many)), 'fill steps')


def test_c2_a_coloured_cell_shows_a_value_not_a_word():
    assert has(forms(heat(rows=[('Billing', ['3', 'ok']), ('Orders', ['2', '5'])]).replace('<td>ok</td>', '<td class="bg-chart-1/40">ok</td>')), 'is not a value')


# ---- C1 diagram

def diagram(elements=None, rels=None, engine=True, extra_svg='', after='', roots=1):
    elements = elements if elements is not None else [('business-actor', 'fill-layer-business', 'Customer'), ('business-process', 'fill-layer-business', 'Order')]
    rels = rels if rels is not None else [('triggering', 'Customer', 'Order')]
    els = ''.join(f'<g data-slot="diagram-element" data-element-type="{t}" class="{c}"><rect x="0" y="0" width="10" height="10"></rect>' + (f'<text>{label}</text>' if label else '') + '</g>' for t, c, label in elements)
    rs = ''.join(f'<g data-slot="diagram-relationship" data-relationship-type="{t}"><line x1="0" y1="0" x2="1" y2="1" marker-end="url(#a)"></line></g>' for t, _, _ in rels)
    svg = f'<svg role="img" aria-label="{len(elements)} elements"><defs><marker id="a"><path d="M0 0"></path></marker></defs>{els}{rs}{extra_svg}</svg>'
    root = f'<div data-slot="diagram">{svg}</div>' * roots if engine else svg
    table = '<table data-slot="table"><caption>Elements</caption><tbody>' + ''.join(f'<tr><td>{e[2]}</td></tr>' for e in elements) + '</tbody></table>'
    return '<div data-entelim-form="c1">' + SCROLL.format('Diagram,', root) + table + '</div>' + after


def test_c1_a_diagram_on_the_one_engine_passes():
    assert forms(diagram()) == []


def test_c1_element_and_relationship_types_come_from_the_archimate_list():
    assert has(forms(diagram([('swimlane', 'fill-layer-business', 'X')])), "'swimlane' is not an ArchiMate 3.2 element type")
    assert has(forms(diagram(rels=[('connects', 'a', 'b')])), "'connects' is not an ArchiMate 3.2 relationship type")


def test_c1_notation_tokens_only_and_each_layer_in_its_own_colour():
    assert has(forms(diagram([('business-actor', 'fill-blue-500', 'X')])), 'neither a theme token nor a notation token')
    assert has(forms(diagram([('business-actor', 'fill-layer-technology', 'X')])), 'business-layer element but is coloured layer-technology')
    assert forms(diagram([('node', 'fill-layer-technology stroke-layer-technology-emphasis', 'Server')])) == []


def test_c1_every_element_has_a_text_label():
    assert has(forms(diagram([('business-actor', 'fill-layer-business', '')])), 'no text label node')


def test_c1_a_list_alternative_has_one_row_per_element():
    bad = diagram().replace('<tr><td>Order</td></tr>', '')
    assert has(forms(bad), 'no list alternative with 2 rows')


def test_c1_the_diagram_has_the_engines_root_slot():
    assert has(forms(diagram(engine=False)), 'exactly one')
    assert has(forms(diagram(roots=2)), 'exactly one')


def test_c1_shapes_drawn_outside_the_notation_macros_fail():
    assert has(forms(diagram(extra_svg='<rect x="0" y="0" width="5" height="5"></rect>')), 'drawn outside the notation macros')


def test_c1_a_second_engine_fails():
    mermaid = diagram(after='<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script><pre class="mermaid">graph TD; A-->B;</pre>')
    out = forms(mermaid)
    assert has(out, "second diagram engine's script") and has(out, 'class "mermaid"')
    cy = diagram(after='<div id="cy"></div><script>var cy = cytoscape({container: document.getElementById("cy")});</script>')
    assert has(forms(cy), 'inline script that drives a second diagram engine')
    flow = diagram(after='<div class="react-flow__renderer"></div>')
    assert has(forms(flow), 'react-flow')
    # the page carries no diagram region at all and still draws one by hand
    page = '<svg><line x1="0" y1="0" x2="9" y2="9" marker-end="url(#a)"></line></svg><div data-panzoom="true"></div><script src="/static/vendor/svg-pan-zoom.min.js"></script>'
    out = forms(page)
    assert has(out, 'edge drawn outside the diagram engine') and has(out, 'pan-and-zoom surface') and has(out, 'second diagram engine')


# ---- C3 timeline

def timeline(axis=True, ticks=('Q1', 'Q2', 'Q3'), bars=None, today=True, table=True, bar_extra=''):
    bars = bars if bars is not None else [('Platform', '--x:10%;--w:30%', '2026-01-01', '2026-03-31'), ('Rollout', '--x:40%;--w:20%', '2026-04-01', '2026-05-31')]
    ax = '<div data-slot="timeline-axis" aria-label="Time, 2026">' + ''.join(f'<span data-slot="timeline-tick">{t}</span>' for t in ticks) + '</div>' if axis else ''
    rows = ''.join(f'<div data-slot="timeline-row"><div data-slot="timeline-bar" style="{st}" data-start="{s}" data-end="{e}" {bar_extra}>{n}</div></div>' for n, st, s, e in bars)
    td = '<div data-slot="timeline-today">Today, 24 Oct</div>' if today else ''
    tbl = '<table><caption>Work packages</caption><tbody>' + ''.join(f'<tr><td>{n}</td><td>{s}</td><td>{e}</td></tr>' for n, _, s, e in bars) + '</tbody></table>' if table else ''
    return '<div data-entelim-form="c3">' + SCROLL.format('Roadmap,', f'<div data-slot="timeline">{ax}{rows}{td}</div>') + tbl + '</div>'


def test_c3_a_labelled_axis_and_bars_on_x_and_w_pass():
    assert forms(timeline()) == []


def test_c3_the_time_axis_is_labelled():
    assert has(forms(timeline(axis=False)), 'no time axis')
    assert has(forms(timeline(ticks=('Q1',))), '1 labelled ticks')
    assert has(forms(timeline(ticks=('', ''))), '0 labelled ticks')


def test_c3_positions_use_x_and_w():
    assert has(forms(timeline(bars=[('Platform', '--x:10%', '2026-01-01', '2026-03-31'), ('Rollout', '--x:40%;--w:20%', '2026-04-01', '2026-05-31')])), 'must use --w')
    assert has(forms(timeline(bars=[('Platform', '--w:10%', '2026-01-01', '2026-03-31'), ('Rollout', '--x:40%;--w:20%', '2026-04-01', '2026-05-31')])), 'must use --x')
    out = forms(timeline(bars=[('Platform', 'left:10%;width:30%', '2026-01-01', '2026-03-31'), ('Rollout', '--x:40%;--w:20%', '2026-04-01', '2026-05-31')]))
    assert has(out, 'must use --x') and has(out, "inline style property ['left', 'width']")
    assert has(forms(timeline(bar_extra='class="left-[12%] w-[30%]"')), 'arbitrary class')
    assert has(forms(timeline(bars=[('Platform', '--x:abc;--w:30%', '2026-01-01', '2026-03-31'), ('Rollout', '--x:40%;--w:20%', '2026-04-01', '2026-05-31')])), 'not a number')


def test_c3_today_marker_and_list_view():
    assert has(forms(timeline(today=False)), 'no today marker')
    assert has(forms(timeline(table=False)), 'no List view table')
    wrong = timeline().replace('<td>2026-03-31</td>', '<td>2026-03-30</td>')
    assert has(forms(wrong), 'data-end=2026-03-31')


# ---- C5 document

def document(html):
    return '<div data-entelim-form="c5">' + html + '</div>'


GOOD_DOC = document('<h1>Solution architecture</h1><h2>1. Summary</h2><p>Use the managed queue.</p><h3>1.1 Why</h3><h2>2. Options</h2><h3>2.1 A</h3><h3>2.2 B</h3><h2>3. Decision</h2>')


def test_c5_ordered_headings_and_answer_first_pass():
    assert forms(GOOD_DOC) == []


def test_c5_heading_order_never_skips_a_level():
    assert has(forms(document('<h1>T</h1><h2>Summary</h2><h4>Deep</h4>')), 'skips a level')
    assert has(forms(document('<h1>T</h1><h1>Again</h1><h2>Summary</h2>')), '2 <h1>')
    assert has(forms(document('<h2>Summary</h2><h3>x</h3>')), '0 <h1>')


def test_c5_numbered_headings_have_no_gaps():
    assert has(forms(document('<h1>T</h1><h2>1. Summary</h2><h2>3. Options</h2>')), 'gap')
    assert has(forms(document('<h1>T</h1><h2>1. Summary</h2><h3>1.1 A</h3><h3>1.3 C</h3>')), 'gap')
    assert forms(document('<h1>T</h1><h2>1. Summary</h2><h3>1.1 A</h3><h2>2. Options</h2><h3>2.1 B</h3>')) == []


def test_c5_the_answer_comes_first():
    assert has(forms(document('<h1>T</h1><h2>Background</h2><h2>Summary</h2>')), 'is not the summary or the answer')
    assert has(forms(document('<h1>T</h1><table><tr><td>1</td></tr></table><h2>Summary</h2>')), 'before the answer')
    assert forms(document('<h1>T</h1><h2>Recommendation</h2>')) == []
    assert forms(document('<h1>T</h1><h2>Background</h2>').replace('<h2>', '<h2 data-answer-first>')) == []


# ---- form markers

def test_an_unknown_form_and_a_missing_form_are_named():
    assert has(forms('<div data-entelim-form="c9"></div>'), 'not a Tier C form')
    out = pg.check_forms(doc('<p>x</p>'), force='c4')[0]
    assert has(out, 'no region marked')


def test_marked_regions_pass_the_generic_page_check():
    text = '<!doctype html><html><head></head><body><main>' + canvas() + diagram() + '</main></body></html>'
    res, _, counts = cp.check(lxml_html.fromstring(text), None, None, LIMITS)
    assert {k: v[:3] for k, v in res.items() if v} == {}, res
    assert counts['regions'] == 2


def test_notation_tokens_are_allowed_inside_a_region_and_in_a_badge_only():
    outside = '<html><body><main><div class="bg-layer-business">x</div></main></body></html>'
    assert cp.check(lxml_html.fromstring(outside), None, None, LIMITS)[0]['colours']
    inside = '<html><body><main><div data-entelim-form="c2"><div class="bg-layer-business">x</div></div></main></body></html>'
    assert cp.check(lxml_html.fromstring(inside), None, None, LIMITS)[0]['colours'] == []


# ---------------------------------------------------------------- help-and-overlays

def help_(body):
    return pg.check_help_text(doc(body))


@pytest.mark.parametrize('text', ['Nothing here yet', 'No data', 'N/A', 'nothing here yet.', 'Status: N/A'])
def test_placeholder_words_fail(text):
    assert help_(f'<p>{text}</p>')['placeholders']


@pytest.mark.parametrize('text', ['No customer segments yet. Add the groups you sell to.', 'Data lake', 'Panama', 'Price 1/2, na'])
def test_other_words_pass(text):
    assert help_(f'<p>{text}</p>')['placeholders'] == []


def test_placeholder_words_in_script_or_hidden_text_are_not_visible_text():
    assert help_('<script>var s = "No data"</script><template><p>N/A</p></template><p hidden>No data</p>')['placeholders'] == []


TIP = '<div data-slot="tooltip"><button data-slot="tooltip-trigger" aria-label="Add"><svg></svg></button><div data-slot="tooltip-content" role="tooltip">Add</div></div>'


def test_icon_only_button_with_name_and_tooltip_passes():
    assert help_(TIP)['icon-buttons'] == []
    sr = '<div><button data-slot="tooltip-trigger"><svg></svg><span class="sr-only">Expand</span></button><div data-slot="tooltip-content">Expand</div></div>'
    assert help_(sr)['icon-buttons'] == []


def test_icon_only_button_without_a_name_fails():
    out = help_('<div><button data-slot="tooltip-trigger"><svg></svg></button><div data-slot="tooltip-content">Add</div></div>')['icon-buttons']
    assert has(out, 'no accessible name')


def test_icon_only_button_without_a_tooltip_fails():
    out = help_('<button aria-label="Add"><svg></svg></button>')['icon-buttons']
    assert has(out, 'no Tooltip') and not has(out, 'no accessible name')
    assert has(help_('<button data-slot="button" data-size="icon" aria-label="x"></button>')['icon-buttons'], 'no Tooltip')


def test_a_button_with_visible_text_needs_no_tooltip():
    assert help_('<button><svg></svg> Save</button>')['icon-buttons'] == []
    assert help_('<button aria-hidden="true"><svg></svg></button>')['icon-buttons'] == []


def test_native_title_tooltips_fail_on_controls():
    assert help_('<button title="Delete">Delete</button>')['native-titles']
    assert help_('<a href="/x" title="Open">Open</a>')['native-titles']
    assert help_('<input title="Name">')['native-titles']
    assert help_('<p title="x">text</p>')['native-titles'] == []


def heatcells(cells, legend=''):
    return '<div data-measure="maturity">' + legend + ''.join(f'<div class="{c}">{t}</div>' for c, t in cells) + '</div>'


def test_r16_an_ordered_measure_shows_its_value_and_a_legend():
    ok = heatcells([('bg-chart-1/20', '1'), ('bg-chart-1/60', '3')], '<div data-legend><span data-slot="badge">1 low</span><span data-slot="badge">5 high</span></div>')
    assert help_(ok)['R16'] == []


def test_r16_a_coloured_cell_without_its_value_fails():
    legend = '<div data-legend></div>'
    out = help_(heatcells([('bg-chart-1/20', ''), ('bg-chart-1/60', '3')], legend))['R16']
    assert has(out, 'without its value as text')
    assert has(help_(heatcells([('bg-chart-1/20', '—'), ('bg-chart-1/60', '3')], legend))['R16'], 'without its value as text')


def test_r16_a_missing_legend_fails():
    out = help_(heatcells([('bg-chart-1/20', '1'), ('bg-chart-1/60', '3')]))['R16']
    assert has(out, 'no legend')
    assert help_(heatcells([('bg-chart-1/20', '1'), ('bg-chart-1/60', '3')], '<div role="group" aria-label="Legend: maturity"></div>'))['R16'] == []


def test_r16_a_single_tint_is_a_zone_not_a_measure():
    assert help_('<div class="bg-chart-2/10 border-chart-2/30">Customer segments</div>')['R16'] == []
    assert help_('<button class="hover:bg-primary/90 bg-primary">Save</button><div class="bg-chart-1/20 hover:bg-chart-1/60">x</div>')['R16'] == []
