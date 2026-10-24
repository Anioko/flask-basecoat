"""Gates the page check runs beyond its structural checks (criteria-v3, library rulings R9, R15 and R16,
help-and-overlays-v1). check_page.py is the one page checker; this module holds the gates it dispatches to.

  A2   structure     the page's element tree against its named original's golden render, repeated rows, cards and
                     list items collapsed to one each: percent match and the first differing node
  A5   pixels        masked screenshot comparison with the golden render (text runs, chart plots, avatars and images
                     painted out), 1440 and 390 wide, light and dark
  B9   charts        each chart spec names a pinned chart id; the chart is that family, has no more series than the
                     original, and is coloured by chart-1 to chart-5 (plus muted-foreground and the colours the pinned
                     chart itself carries)
  R9   a11y          axe: serious and critical findings fail even where the original has them, unless the page records
                     a departure; moderate and minor findings fail only beyond the original's
  C    forms         one gate per Tier C form inside an element marked data-entelim-form (C1 diagram, C2 heat map,
                     C3 timeline, C4 canvas, C5 document); C1 also enforces the one diagram engine (R15)
  help text          placeholder words, icon-only buttons (name and Tooltip), native title tooltips, and R16 (an ordered
                     measure drawn in colour also shows its value as text, with a legend)

Every gate takes a parsed lxml document and returns a list of failure lines; an empty list is a pass.
"""
import contextlib
import difflib
import io
import json
import pathlib
import re
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance' / 'golden' / 'out'
CHART_DATA = ROOT / 'flask_basecoat' / 'data' / 'charts'

SKIP_TAGS = {'script', 'style', 'template', 'noscript', 'link', 'meta', 'title', 'head'}


def elements(root):
    return [e for e in root.iter() if isinstance(e.tag, str)]


def closed_floating(el):
    """Closed menus, popovers and dialogs: React renders them only while open, so they are not part of the frame."""
    for a in [el] + list(el.iterancestors()):
        if not isinstance(a.tag, str):
            continue
        s = a.get('data-slot') or ''
        if a.get('data-state') == 'closed' and s.endswith(('-content', '-overlay', '-portal')):
            return True
    return False


def in_template(el):
    return any(isinstance(a.tag, str) and a.tag in ('template', 'script', 'style', 'noscript') for a in el.iterancestors())


def own_text(el):
    return ' '.join(t.strip() for t in el.xpath('./text()') if t.strip())


def all_text(el, sr_only=True):
    """Text of an element and its descendants, outside script, style and template; optionally without sr-only text."""
    out = []

    def walk(e):
        if not isinstance(e.tag, str) or e.tag in ('script', 'style', 'template', 'noscript'):
            return
        if not sr_only and 'sr-only' in (e.get('class') or '').split():
            return
        if e.get('hidden') is not None:
            return
        if e.text and e.text.strip():
            out.append(e.text.strip())
        for c in e:
            walk(c)
            if c.tail and c.tail.strip():
                out.append(c.tail.strip())
    walk(el)
    return ' '.join(out)


def describe(el):
    s = el.get('data-slot')
    cls = (el.get('class') or '')[:60]
    return f"<{el.tag}{' data-slot=' + s if s else ''} class=\"{cls}\">"


def classes(el):
    return (el.get('class') or '').split()


def strip_variant(c):
    return c.split(':')[-1].lstrip('!')


# ================================================================ departures (R9)

def load_departures(doc, path=None):
    """Recorded departures: `<meta name="shadcn-departure" content="R9 color-contrast wcag=1.4.3 reason=...">` in the
    page, or a JSON file of {"check": "R9", "rule": "color-contrast", "wcag": "1.4.3", "reason": "..."}. A record without
    a rule, a WCAG criterion and a reason is not a record."""
    records = []
    for m in doc.xpath('//meta[@name="shadcn-departure"]'):
        c = m.get('content') or ''
        mm = re.match(r'\s*(\S+)\s+(\S+)\s+wcag=(\S+)\s+reason=(.+)$', c)
        if mm:
            records.append({'check': mm.group(1), 'rule': mm.group(2), 'wcag': mm.group(3), 'reason': mm.group(4).strip()})
    if path:
        records += json.loads(pathlib.Path(path).read_text(encoding='utf8'))
    return [r for r in records if r.get('rule') and r.get('wcag') and r.get('reason')]


# ================================================================ A2 structure

LEAF_SLOTS = {'chart', 'sidebar-header'}  # drawn by the runtime / a brand slot compared by slot, not by content


def norm_tree(el, prune=()):
    """(label, children): text, attributes and icon internals dropped, repeated identical sibling units collapsed."""
    slot = el.get('data-slot')
    label = f'{el.tag}[{slot}]' if slot else el.tag
    if el.tag == 'svg' or slot in LEAF_SLOTS or el in prune:
        return (label if el not in prune else 'content', ())
    kids = []
    for c in el:
        if not isinstance(c.tag, str) or c.tag in SKIP_TAGS or closed_floating(c):
            continue
        k = norm_tree(c, prune)
        if not kids or kids[-1] != k:
            kids.append(k)
    return (label, tuple(kids))


def flatten(tree):
    """Preorder tokens 'depth:label' and, for each, the path of ancestors that leads to it."""
    toks, paths = [], []

    def walk(t, depth, path):
        toks.append(f'{depth}:{t[0]}')
        paths.append(' > '.join(path + [t[0]]))
        for c in t[1]:
            walk(c, depth + 1, path + [t[0]])
    walk(tree, 0, [])
    return toks, paths


def _match(a_tree, b_tree):
    a, pa = flatten(a_tree)
    b, pb = flatten(b_tree)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    matched = sum(m.size for m in sm.get_matching_blocks())
    first = None
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            first = {'kind': tag,
                     'page': a[i1].split(':', 1)[1] if i1 < len(a) else None,
                     'page_path': pa[i1] if i1 < len(pa) else (pa[-1] if pa else ''),
                     'original': b[j1].split(':', 1)[1] if j1 < len(b) else None,
                     'original_path': pb[j1] if j1 < len(pb) else (pb[-1] if pb else '')}
            break
    return len(a), len(b), matched, first


def structure_match(doc, original, content_roots):
    """A2 (whole page) and B2 (frame only: the content area is pruned from both trees)."""
    body, obody = doc.xpath('//body')[0], original.xpath('//body')[0]
    na, nb, matched, first = _match(norm_tree(body), norm_tree(obody))
    percent = round(100 * matched / max(na, nb, 1), 2)
    ocontent = content_roots(original)
    fa, fb, fm, ffirst = _match(norm_tree(body, set(content_roots(doc))), norm_tree(obody, set(ocontent)))
    return {'percent': percent, 'nodes_page': na, 'nodes_original': nb, 'matched': matched, 'first_difference': first,
            'frame_percent': round(100 * fm / max(fa, fb, 1), 2), 'frame_first_difference': ffirst}


def check_structure(doc, original, content_roots, tier='B'):
    """Tier A needs 100% of the tree; Tier B and C need 100% of the frame (B2) and report the whole-page figure."""
    if original is None:
        return ['no original named: pass --nearest or add <meta name="shadcn-nearest">'], {}
    r = structure_match(doc, original, content_roots)
    out = []
    fd = r['first_difference']
    if tier.upper() == 'A' and r['percent'] < 100:
        out.append(f"structure matches {r['percent']}% of {max(r['nodes_page'], r['nodes_original'])} nodes (Tier A needs 100%); first differing node: "
                   f"page {fd['page']!r} at {fd['page_path']} vs original {fd['original']!r} at {fd['original_path']}")
    if r['frame_percent'] < 100:
        f = r['frame_first_difference']
        out.append(f"frame matches {r['frame_percent']}% (B2 needs 100%); first differing frame node: page {f['page']!r} at {f['page_path']} vs original {f['original']!r}")
    return out, r


# ================================================================ browser plumbing

@contextlib.contextmanager
def local_server(html_text=None):
    """The bare test app with the examples and gallery on a loopback port; serves html_text at /__page when given."""
    from werkzeug.serving import make_server
    from flask_basecoat.testing import make_app
    from flask_basecoat.examples import examples_bp
    app = make_app()
    if 'basecoat_examples' not in app.blueprints:
        app.register_blueprint(examples_bp, url_prefix='/examples')
    if html_text is not None:
        @app.route('/__page')
        def _page():
            return html_text
    srv = make_server('127.0.0.1', 0, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f'http://127.0.0.1:{srv.server_port}'
    finally:
        srv.shutdown()


def page_urls(target, text, nearest, golden_rel):
    """(context manager yielding (page_url, golden_url or None))."""
    @contextlib.contextmanager
    def cm():
        if target.startswith(('http://', 'https://')):
            from urllib.parse import urlsplit
            u = urlsplit(target)
            base = f'{u.scheme}://{u.netloc}'
            yield target, (f'{base}/basecoat/golden/{golden_rel}' if golden_rel else None)
            return
        is_file = target.endswith('.html') and pathlib.Path(target).exists()
        with local_server(text if is_file else None) as base:
            yield base + ('/__page' if is_file else target), (f'{base}/basecoat/golden/{golden_rel}' if golden_rel else None)
    return cm()


def goto(page, url, theme):
    page.goto(url + (('&' if '?' in url else '?') + f'theme={theme}'), wait_until='load')
    page.evaluate(f"document.documentElement.classList.toggle('dark', {str(theme == 'dark').lower()})")
    page.add_style_tag(content='*,*::before,*::after{transition:none!important;animation:none!important;caret-color:transparent!important}')
    try:
        page.wait_for_function("""() => Array.from(document.querySelectorAll('[data-slot="chart"]')).every((c) => { const s = c.querySelector('svg.recharts-surface'); return s && s.getBoundingClientRect().width > 0; })""", timeout=4000)
    except Exception:  # noqa: BLE001 - a chart that does not draw is B9's finding
        pass
    page.wait_for_timeout(250)


# ================================================================ A5 masked pixels

MASK_JS = r"""(region) => {
  const GREY = '#808080', doc = document.documentElement;
  const box = (r, z) => { const d = document.createElement('div'); d.setAttribute('data-pixel-mask', '');
    d.style.cssText = `position:absolute;left:${r.left + scrollX}px;top:${r.top + scrollY}px;width:${r.width}px;height:${r.height}px;background:${GREY};z-index:2147483647;pointer-events:none`; document.body.appendChild(d); };
  const rects = [];
  // text runs
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (!n.textContent.trim()) continue;
    const p = n.parentElement; if (!p || /^(SCRIPT|STYLE|TEMPLATE|NOSCRIPT)$/.test(p.tagName)) continue;
    const cs = getComputedStyle(p); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const range = document.createRange(); range.selectNodeContents(n);
    for (const r of range.getClientRects()) if (r.width > 0 && r.height > 0) rects.push(r);
  }
  // chart plots, avatars and images
  for (const el of document.querySelectorAll('[data-slot="chart"], [data-slot="avatar"], img, video, canvas, picture')) {
    const r = el.getBoundingClientRect(); if (r.width > 0 && r.height > 0) rects.push(r);
  }
  // the content area, when only the frame is compared (B8)
  if (region === 'frame') {
    const inset = document.querySelector('[data-slot="sidebar-inset"]');
    if (inset) for (const c of inset.children) if (c.tagName !== 'HEADER') { const r = c.getBoundingClientRect(); if (r.width > 0) rects.push(r); }
  }
  for (const r of rects) box(r);
  return rects.length;
}"""


def png_diff(a_png, b_png, tolerance=12):
    """Percent of pixels that differ by more than `tolerance` in any channel; a missing area counts as different."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(io.BytesIO(a_png)).convert('RGB')).astype(int)
    b = np.asarray(Image.open(io.BytesIO(b_png)).convert('RGB')).astype(int)
    h, w = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])

    def pad(x):
        out = np.full((h, w, 3), -1000, dtype=int)
        out[:x.shape[0], :x.shape[1]] = x
        return out
    d = np.abs(pad(a) - pad(b)).max(axis=2) > tolerance
    return round(100 * d.sum() / (h * w), 3)


PIXEL_LIMITS = {'A': 0.5, 'B': 2.0, 'C': 2.0}  # A5; B8 (frame region)
VIEWPORTS = (('1440', 1440, 900), ('390', 390, 844))


def check_pixels(page_url, golden_url, tier='B', region=None):
    """A5 for Tier A (whole page) and B8 for Tier B and C (the frame; the content area is painted out)."""
    from playwright.sync_api import sync_playwright
    if golden_url is None:
        return ['no golden render to compare with'], {}
    region = region or ('page' if tier.upper() == 'A' else 'frame')
    limit = PIXEL_LIMITS[tier.upper()]
    out, info = [], {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for theme in ('light', 'dark'):
            for label, w, h in VIEWPORTS:
                shots = []
                for url in (page_url, golden_url):
                    pg = b.new_page(viewport={'width': w, 'height': h})
                    goto(pg, url, theme)
                    pg.evaluate(MASK_JS, region)
                    shots.append(pg.screenshot(full_page=True))
                    pg.close()
                pct = png_diff(*shots)
                info[f'{theme} {label}'] = pct
                if pct > limit:
                    out.append(f'[{theme} {label}px] {pct}% of masked pixels differ from the golden render (limit {limit}%, region {region})')
        b.close()
    return out, info


# ================================================================ R9 strict accessibility

AXE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']
AXE_RUN = """async ([disabled, tags]) => {
    const rules = {}; disabled.forEach((r) => { rules[r] = { enabled: false }; });
    const r = await axe.run(document, { runOnly: { type: 'tag', values: tags }, rules });
    return r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, count: v.nodes.length, nodes: v.nodes.slice(0, 5).map((n) => n.target.join(' ')) }));
}"""
SEVERE = ('serious', 'critical')


def axe_scan(pg, url, theme, axe_src, disabled):
    goto(pg, url, theme)
    pg.add_script_tag(content=axe_src)
    return pg.evaluate(AXE_RUN, [disabled, AXE_TAGS])


def judge_a11y(ours, golden, departures):
    """Serious and critical: every finding fails unless the page records a departure for the rule. Moderate and minor:
    fail only where the page has more nodes with the rule than the original."""
    recorded = {d['rule'] for d in departures if d.get('check', 'R9') in ('R9', 'X9')}
    gold = {v['id']: v['count'] for v in golden}
    out = []
    for v in ours:
        if v['impact'] in SEVERE:
            if v['id'] not in recorded:
                out.append(f"{v['id']} ({v['impact']}) x{v['count']}: {v['help']} -> {v['nodes'][:2]}"
                           + (' [the original has it too; R9 fixes it or records a departure]' if v['id'] in gold else ''))
        elif v['count'] > gold.get(v['id'], 0):
            out.append(f"{v['id']} ({v['impact']}) x{v['count']} beyond the original's x{gold.get(v['id'], 0)}: {v['help']} -> {v['nodes'][:2]}")
    return out


def check_a11y_strict(page_url, golden_url, departures):
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import check_a11y
    axe_src = check_a11y.AXE.read_text(encoding='utf8')
    out, info = [], {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for theme in ('light', 'dark'):
            for label, w, h in VIEWPORTS:
                pg = b.new_page(viewport={'width': w, 'height': h})
                ours = axe_scan(pg, page_url, theme, axe_src, check_a11y.DISABLED)
                gold = axe_scan(pg, golden_url, theme, axe_src, check_a11y.DISABLED) if golden_url else []
                pg.close()
                for line in judge_a11y(ours, gold, departures):
                    out.append(f'[{theme} {label}px] {line}')
                info[f'{theme} {label}'] = {'findings': len(ours), 'original': len(gold)}
        b.close()
    if departures:
        info['departures'] = [f"{d['rule']} (WCAG {d['wcag']})" for d in departures]
    return out, info


# ================================================================ B9 charts

FAMILY_CLASS = {'AreaChart': 'recharts-area', 'BarChart': 'recharts-bar', 'LineChart': 'recharts-line', 'PieChart': 'recharts-pie',
                'RadarChart': 'recharts-radar', 'RadialBarChart': 'recharts-radial-bar'}
CHART_TOKENS = {f'--chart-{i}' for i in range(1, 6)} | {'--muted-foreground'}
VAR_RE = re.compile(r'var\((--[\w-]+)')
LITERAL_COLOUR_RE = re.compile(r'#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\boklch\(|\boklab\(|\blab\(|\blch\(')


def pinned_spec(chart_id):
    f = CHART_DATA / f'{chart_id}.json'
    return json.loads(f.read_text(encoding='utf8')) if f.exists() else None


def series_count(spec):
    s = spec.get('series') or []
    if len(s) == 1 and s[0].get('cells'):
        return len(s[0]['cells'])
    return len(s)


def spec_colours(spec):
    """(tokens, literals): the `var(--x)` names and raw colour literals anywhere in a spec outside its data and labels.
    var(--color-<key>) is the chart config's own indirection; the config's colours are scanned instead."""
    keys = set((spec.get('config') or {}))
    tokens, literals = set(), set()

    def walk(o, skip=False):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ('data', 'label', 'labels'):
                    continue
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            for t in VAR_RE.findall(o):
                if not (t.startswith('--color-') and t[len('--color-'):] in keys):
                    tokens.add(t)
            if LITERAL_COLOUR_RE.search(o):
                literals.add(o)
    walk({k: v for k, v in spec.items() if k not in ('data',)})
    return tokens, literals


def chart_specs(doc):
    out = []
    for c in doc.xpath('//*[@data-slot="chart"]'):
        sc = c.xpath('.//script[@data-chart-spec]')
        spec = None
        if sc:
            try:
                spec = json.loads(sc[0].text or '')
            except ValueError:
                spec = None
        out.append((c, spec))
    return out


def check_charts_static(doc):
    out, info = [], []
    for c, spec in chart_specs(doc):
        name = c.get('data-chart') or describe(c)
        if spec is None:
            out.append(f'{name}: no readable chart spec (script[data-chart-spec])')
            continue
        cid = spec.get('chart')
        if not cid:
            out.append(f'{name}: the spec names no pinned chart id (set "chart": "<chart id>", e.g. "chart-area-interactive")')
            continue
        pin = pinned_spec(cid)
        if pin is None:
            out.append(f'{name}: "{cid}" is not a pinned chart id')
            continue
        fam, pfam = spec.get('component'), pin.get('component')
        sfam = sorted(s.get('component', '') for s in spec.get('series') or [])
        psfam = sorted(s.get('component', '') for s in pin.get('series') or [])
        if fam != pfam or set(sfam) != set(psfam):
            out.append(f'{name}: not the {cid} family (is {fam} with {sorted(set(sfam))}; the original is {pfam} with {sorted(set(psfam))})')
        n, pn = series_count(spec), series_count(pin)
        if n > pn:
            out.append(f'{name}: {n} series; {cid} has {pn}')
        if n > 5:
            out.append(f'{name}: {n} series; at most 5')
        toks, lits = spec_colours(spec)
        ptoks, plits = spec_colours(pin)
        for t in sorted(toks - CHART_TOKENS - ptoks):
            out.append(f'{name}: colour token var({t}) is not chart-1 to chart-5 (nor muted-foreground, nor a colour {cid} carries)')
        for l in sorted(lits - plits):
            out.append(f'{name}: raw colour {l!r} in the spec')
        info.append({'chart': name, 'id': cid, 'family': fam, 'series': n, 'original_series': pn})
    return out, info


def check_charts_rendered(page_url):
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1440, 'height': 900})
        goto(pg, page_url, 'light')
        for c in pg.query_selector_all('[data-slot="chart"]'):
            comp = pg.evaluate("""(c) => { const s = c.querySelector('script[data-chart-spec]'); try { return JSON.parse(s.textContent).component; } catch (e) { return null; } }""", c)
            want = FAMILY_CLASS.get(comp)
            drawn = pg.evaluate("""(c) => !!c.querySelector('svg.recharts-surface')""", c)
            if not drawn:
                out.append(f'{c.get_attribute("data-chart")}: the chart did not draw')
            elif want and not pg.evaluate("""([c, w]) => !!c.querySelector('.' + w)""", [c, want]):
                out.append(f'{c.get_attribute("data-chart")}: rendered chart has no {want} element; it is not a {comp}')
        b.close()
    return out


# ================================================================ help-and-overlays-v1

PLACEHOLDER_RE = re.compile(r'Nothing here yet|\bNo data\b|(?<![\w/])N/A(?![\w/])', re.I)
CONTROL_SLOT_RE = re.compile(r'^(?:button|tooltip-trigger|toggle|toggle-group-item|sidebar-trigger|carousel-previous|carousel-next|dropdown-menu-trigger|popover-trigger|dialog-trigger|sheet-trigger)$')
CONTROLS = {'button', 'a', 'input', 'select', 'textarea', 'summary'}
CONTROL_ROLES = {'button', 'link', 'tab', 'switch', 'checkbox', 'radio', 'menuitem', 'combobox', 'option', 'slider'}


def visible_nodes(doc):
    for el in elements(doc.xpath('//body')[0]):
        if el.tag in SKIP_TAGS or in_template(el) or el.get('hidden') is not None:
            continue
        yield el


def check_placeholders(doc):
    out = []
    for el in visible_nodes(doc):
        t = own_text(el)
        m = PLACEHOLDER_RE.search(t) if t else None
        if m:
            out.append(f'placeholder text {m.group(0)!r} in {describe(el)}: say what is missing and what to do')
    return out


def is_control(el):
    return el.tag in CONTROLS and (el.tag != 'a' or el.get('href') is not None) or el.get('role') in CONTROL_ROLES


def icon_only_buttons(doc):
    for el in visible_nodes(doc):
        slot = el.get('data-slot') or ''
        if not (el.tag == 'button' or el.get('role') == 'button' or CONTROL_SLOT_RE.match(slot)):
            continue
        if el.tag in ('input', 'select', 'textarea') or el.get('type') == 'hidden' or el.get('aria-hidden') == 'true' or el.get('role') in ('combobox', 'listbox'):
            continue
        if any(a.get('aria-hidden') == 'true' for a in el.iterancestors() if isinstance(a.tag, str)):
            continue
        if all_text(el, sr_only=False).strip():
            continue
        # a Radix trigger asChild renders the button inside the trigger element: judge the innermost one
        if (el.get('data-slot') == 'tooltip-trigger' and el.xpath('.//button')):
            continue
        if el.xpath('.//svg | .//img') or (el.get('data-size') or '').startswith('icon'):
            yield el


def accessible_name(el, doc):
    if (el.get('aria-label') or '').strip():
        return el.get('aria-label').strip()
    ids = (el.get('aria-labelledby') or '').split()
    names = [all_text(t[0]) for i in ids if (t := doc.xpath(f'//*[@id="{i}"]'))]
    if any(names):
        return ' '.join(names)
    return all_text(el)  # includes sr-only text


def has_tooltip(el, doc):
    t = el if el.get('data-slot') == 'tooltip-trigger' else next((a for a in el.iterancestors() if a.get('data-slot') == 'tooltip-trigger'), None)
    if t is not None:
        parent = t.getparent()
        if parent is not None and any(s.get('data-slot') == 'tooltip-content' for s in parent if s is not t):
            return True
    d = (el.get('aria-describedby') or '').split()
    return any(doc.xpath(f'//*[@id="{i}"][@data-slot="tooltip-content"]') for i in d)


def check_icon_buttons(doc):
    out = []
    for el in icon_only_buttons(doc):
        if not accessible_name(el, doc):
            out.append(f'icon-only button has no accessible name: {describe(el)}')
        if not has_tooltip(el, doc):
            out.append(f'icon-only button has no Tooltip: {describe(el)}' + (f' ("{accessible_name(el, doc)}")' if accessible_name(el, doc) else ''))
    return out


def check_native_titles(doc):
    out = []
    for el in visible_nodes(doc):
        if (el.get('title') or '').strip() and (is_control(el) or CONTROL_SLOT_RE.match(el.get('data-slot') or '')):
            out.append(f'native title tooltip "{el.get("title")[:40]}" on {describe(el)}: use a Tooltip')
    return out


RAMP_RE = re.compile(r'^bg-(chart-[1-5])/(20|30|40|50|60|70|80|90|100)$')  # a step of the ordered ramp; /10 is the zone tint, and hover: and dark: variants do not count
LEGEND_RE = re.compile(r'legend', re.I)


def has_legend(scope, doc):
    for el in elements(scope) + [scope]:
        if el.get('data-legend') is not None or el.get('data-slot') in ('chart-legend', 'legend'):
            return True
        for attr in ('aria-label', 'data-testid'):
            if LEGEND_RE.search(el.get(attr) or ''):
                return True
        for i in (el.get('aria-labelledby') or '').split():
            if any(LEGEND_RE.search(all_text(t)) for t in doc.xpath(f'//*[@id="{i}"]')):
                return True
    return False


def check_ordered_measure(doc):
    """R16: an ordered measure drawn in colour (two or more opacity steps of one chart token in one place, or an element
    marked data-measure) also shows the value as text on each coloured element, and a legend is present. Tints of
    different tokens are categories, and a single /10 tint is a zone; neither is an ordered measure."""
    out = []
    body = doc.xpath('//body')[0]
    groups = {}
    for el in visible_nodes(doc):
        for c in classes(el):
            m = RAMP_RE.match(c)
            if m:
                scope = next((a for a in el.iterancestors() if a.get('data-measure') is not None), None)
                if scope is None:
                    scope = next((a for a in el.iterancestors() if a.tag in ('table', 'tbody') or a.get('data-slot') in ('card', 'card-content')), body)
                groups.setdefault((scope, m.group(1)), []).append((el, m.group(2)))
    for (scope, token), members in groups.items():
        steps = {s for _, s in members}
        if len(steps) < 2:
            continue
        for el, _ in members:
            txt = all_text(el)
            if not txt or re.fullmatch(r'[\s\-–—.]*', txt):
                out.append(f'ordered measure drawn in colour without its value as text: {describe(el)}')
        if not has_legend(scope, doc) and not has_legend(body, doc):
            out.append(f'ordered measure ({len(steps)} steps of {token}) has no legend near {describe(scope)}')
    return out


def check_help_text(doc):
    return {'placeholders': check_placeholders(doc), 'icon-buttons': check_icon_buttons(doc),
            'native-titles': check_native_titles(doc), 'R16': check_ordered_measure(doc)}


# ================================================================ Tier C forms

FORM_ALIASES = {'c1': 'c1', 'diagram': 'c1', 'c2': 'c2', 'matrix': 'c2', 'heat-map': 'c2', 'heatmap': 'c2', 'c3': 'c3', 'timeline': 'c3',
                'c4': 'c4', 'canvas': 'c4', 'board': 'c4', 'c5': 'c5', 'document': 'c5'}
# Slots the Tier C Keep macros emit; allowed only inside a marked region.
FORM_SLOTS = {'diagram', 'diagram-viewport', 'diagram-element', 'diagram-relationship', 'diagram-notation', 'diagram-label',
              'timeline', 'timeline-axis', 'timeline-tick', 'timeline-row', 'timeline-bar', 'timeline-today', 'timeline-milestone',
              'heat-map', 'heat-map-cell', 'canvas', 'canvas-box'}
NOTATION_TOKEN_RE = re.compile(r'^(?:success|warning|layer-(?:motivation|strategy|business|application|technology|implementation|risk))(?:-emphasis)?$')
GEOMETRY_PROPS = {'--x', '--y', '--w', '--h', '--col', '--row'}  # G-5
COLOUR_UTIL_RE = re.compile(r'^(?:bg|text|border|ring|fill|stroke|from|via|to)-(?P<name>[a-z]+(?:-[a-z0-9]+)*?)(?:/\d+)?$')
THEME_TOKENS = {'background', 'foreground', 'card', 'card-foreground', 'popover', 'popover-foreground', 'primary', 'primary-foreground',
                'secondary', 'secondary-foreground', 'muted', 'muted-foreground', 'accent', 'accent-foreground', 'destructive', 'border',
                'input', 'ring', 'chart-1', 'chart-2', 'chart-3', 'chart-4', 'chart-5', 'transparent', 'current'}


def form_regions(doc):
    out = []
    for el in doc.xpath('//*[@data-entelim-form]'):
        raw = (el.get('data-entelim-form') or '').strip().lower()
        out.append((FORM_ALIASES.get(raw), raw, el))
    return out


def style_props(style):
    return {d.split(':', 1)[0].strip().lower() for d in (style or '').split(';') if ':' in d}


def shared_form_checks(region, form):
    """Shared conditions of 1.5: geometry only through the G-5 custom properties; the scroll region keeps the shape."""
    out = []
    for el in elements(region) + [region]:
        bad = style_props(el.get('style')) - GEOMETRY_PROPS
        if bad and not (el.tag in ('svg', 'circle', 'rect', 'path', 'g') and bad <= {'transform'}):
            out.append(f'inline style property {sorted(bad)} on {describe(el)}: only --x, --y, --w, --h, --col, --row are allowed')
    if form in ('c1', 'c2', 'c3', 'c4'):
        scrollers = [e for e in elements(region) + [region] if any(strip_variant(c) == 'overflow-x-auto' for c in classes(e))]
        if not scrollers:
            out.append('the region has no overflow-x-auto scroll container: on a phone the form must scroll, not stack')
        for s in scrollers:
            if s.get('role') != 'region' or s.get('tabindex') != '0' or not (s.get('aria-label') or s.get('aria-labelledby')):
                out.append(f'scroll container {describe(s)} must be a focusable role="region" with a name')
    return out


# ---- C4 canvas

# Published arrangement: title -> (columns in fifths of the width, rows). The upper area is rows 1-2, the money strip is row 3.
CANVAS_BOXES = {
    'business-model': {
        'Key Partners': ((0, 1), (1, 3)), 'Key Activities': ((1, 2), (1, 2)), 'Key Resources': ((1, 2), (2, 3)),
        'Value Propositions': ((2, 3), (1, 3)), 'Customer Relationships': ((3, 4), (1, 2)), 'Channels': ((3, 4), (2, 3)),
        'Customer Segments': ((4, 5), (1, 3)), 'Cost Structure': ((0, 2.5), (3, 4)), 'Revenue Streams': ((2.5, 5), (3, 4))},
}


def _grid_ncols(el):
    for a in el.iterancestors():
        for c in classes(a):
            m = re.match(r'^(?:[\w@\[\]/-]+:)*grid-cols-(\d+)$', c)
            if m:
                return int(m.group(1))
    return None


def placement(el):
    """(col_start, col_end, row_start, row_end) as 1-based grid lines, from col-start-*, col-span-*, row-start-*, row-span-*
    or the --col and --row custom properties."""
    def line(prefix, prop):
        start = span = None
        for c in classes(el):
            c = strip_variant(c)
            m = re.match(rf'^{prefix}-start-(\d+)$', c)
            if m:
                start = int(m.group(1))
            m = re.match(rf'^{prefix}-span-(\d+)$', c)
            if m:
                span = int(m.group(1))
        m = re.search(rf'{prop}\s*:\s*(\d+)', el.get('style') or '')
        if m:
            start = int(m.group(1))
        return start, span or 1
    cs, cspan = line('col', '--col')
    rs, rspan = line('row', '--row')
    if cs is None or rs is None:
        return None
    return cs, cs + cspan, rs, rs + rspan


def check_canvas(region):
    out = []
    spec = CANVAS_BOXES['business-model']
    boxes = {}
    for card in region.xpath('.//*[@data-slot="card"]'):
        t = card.xpath('./*[@data-slot="card-header"]//*[@data-slot="card-title"] | ./*[@data-slot="card-title"]')
        title = all_text(t[0]).strip() if t else None
        if title is None:
            out.append(f'a box without a CardTitle: {describe(card)}')
            continue
        if title in boxes:
            out.append(f'box "{title}" appears twice')
        boxes[title] = card
    for title in spec:
        if title not in boxes:
            out.append(f'box "{title}" is missing (the published canvas has nine: {", ".join(spec)})')
    for title in boxes:
        if title not in spec:
            out.append(f'box "{title}" is not one of the canvas\'s nine published boxes')
    if len(boxes) != 9:
        out.append(f'{len(boxes)} boxes; the business model canvas has exactly nine')
    ncols = {_grid_ncols(c) for c in boxes.values()}
    ncols.discard(None)
    if not ncols:
        out.append('boxes are not placed in a grid-cols-5 or grid-cols-10 container')
        return out
    n = ncols.pop()
    if ncols or n not in (5, 10):
        out.append(f'the canvas is a 5-column layout (grid-cols-5, or grid-cols-10 so the money strip splits in half); found {sorted({n} | ncols)}')
        return out
    unit = n / 5
    got = {}
    for title, card in boxes.items():
        p = placement(card)
        if p is None:
            if title in spec:
                out.append(f'box "{title}" has no col-start/col-span/row-start/row-span placement')
            continue
        got[title] = (p[0] - 1, p[1] - 1, p[2] - 1, p[3] - 1)
    rows_upper = [g[2] for t, g in got.items() if t in ('Key Activities', 'Key Resources')]
    for title, ((c0, c1), (r0, r1)) in spec.items():
        if title not in got:
            continue
        gc0, gc1, gr0, gr1 = got[title]
        if (gc0 / unit, gc1 / unit) != (c0, c1):
            out.append(f'"{title}" spans columns {gc0 + 1} to {gc1} of {n}; the published canvas puts it at {c0 * unit + 1:g} to {c1 * unit:g} of {n}')
    # rows are checked by relation, so 3-row and finer row grids both pass
    g = got
    need = ['Key Partners', 'Key Activities', 'Key Resources', 'Value Propositions', 'Customer Relationships', 'Channels', 'Customer Segments', 'Cost Structure', 'Revenue Streams']
    if all(t in g for t in need):
        ka, kr = g['Key Activities'], g['Key Resources']
        if not ka[3] <= kr[2]:
            out.append('Key Activities must sit above Key Resources')
        if not g['Customer Relationships'][3] <= g['Channels'][2]:
            out.append('Customer Relationships must sit above Channels')
        top, bottom = min(ka[2], g['Customer Relationships'][2]), max(kr[3], g['Channels'][3])
        for t in ('Key Partners', 'Value Propositions', 'Customer Segments'):
            if (g[t][2], g[t][3]) != (top, bottom):
                out.append(f'"{t}" must span the full height of the upper area (rows {top + 1} to {bottom}); it spans {g[t][2] + 1} to {g[t][3]}')
        for t in ('Cost Structure', 'Revenue Streams'):
            if g[t][2] < bottom:
                out.append(f'"{t}" must sit in the strip below the upper area')
        if g['Cost Structure'][2:] != g['Revenue Streams'][2:]:
            out.append('Cost Structure and Revenue Streams must share the bottom strip')
        # the money strip's row is shorter than the upper rows, so only the upper-area boxes are compared by area
        area = {t: (v[1] - v[0]) * (v[3] - v[2]) for t, v in g.items() if t not in ('Cost Structure', 'Revenue Streams')}
        if any(area[t] > area['Value Propositions'] for t in area):
            out.append('Value Propositions must be the largest box of the upper area')
    return out


# ---- C2 heat map

STEP_RE = re.compile(r'^bg-(?:chart-[1-5]|success|warning|destructive|primary|layer-[a-z]+)(?:/(\d+))?$')
VALUE_RE = re.compile(r'\d|High|Medium|Low|Red|Amber|Green|Yes|No', re.I)
EMPTY_CELL_RE = re.compile(r'^[\s\-–—.]*$|^N/A$|^No data$', re.I)


def table_name(t):
    cap = t.xpath('./caption')
    return (all_text(cap[0]).strip() if cap else '') or (t.get('aria-label') or '').strip()


def check_heat_map(doc, region):
    out = []
    tables = region.xpath('.//table') or doc.xpath('//table[@data-slot="table"]')
    # the alternative must be a real table that is named, with header cells and a rectangular body
    alt = [t for t in tables if table_name(t) and t.xpath('.//th')]
    if not alt:
        out.append('no real table alternative: a named <table> (caption or aria-label) with header cells (HM-1)')
        return out
    t = alt[0]
    rows = t.xpath('./tbody/tr') or t.xpath('./tr')
    widths = {len(r.xpath('./td | ./th')) for r in rows}
    if len(widths) > 1:
        out.append(f'the table is not rectangular: rows have {sorted(widths)} cells (HM-2)')
    if not any(r.xpath('./th') for r in rows):
        out.append('body rows have no row header cell (th scope="row")')
    steps = set()
    for r in rows:
        for cell in r.xpath('./td'):
            txt = all_text(cell).strip()
            if not txt or EMPTY_CELL_RE.match(txt):
                out.append(f'cell carries no text value: {describe(cell)}')
            for c in classes(cell) + [x for d in cell.iterdescendants() if isinstance(d.tag, str) for x in classes(d)]:
                m = STEP_RE.match(strip_variant(c))
                if m:
                    steps.add(strip_variant(c))
                    if txt and not VALUE_RE.search(txt):
                        out.append(f'coloured cell text {txt!r} is not a value (a number, or High, Medium, Low, Red, Amber, Green): {describe(cell)}')
    if len(steps) > 5:
        out.append(f'{len(steps)} fill steps; at most 5 (opacity steps 20, 40, 60, 80, 100 of one chart token, or the RAG tokens)')
    # visual cells outside the table (a grid drawn beside it) must also carry text
    for c in region.xpath('.//*[@data-slot="heat-map-cell"]'):
        if not all_text(c).strip():
            out.append(f'cell carries no text value: {describe(c)}')
    return out


# ---- C1 diagram

ARCHIMATE_LAYERS = {
    'strategy': ['resource', 'capability', 'value-stream', 'course-of-action'],
    'business': ['business-actor', 'business-role', 'business-collaboration', 'business-interface', 'business-process', 'business-function',
                 'business-interaction', 'business-event', 'business-service', 'business-object', 'contract', 'representation', 'product'],
    'application': ['application-component', 'application-collaboration', 'application-interface', 'application-function',
                    'application-interaction', 'application-process', 'application-event', 'application-service', 'data-object'],
    'technology': ['node', 'device', 'system-software', 'technology-collaboration', 'technology-interface', 'path', 'communication-network',
                   'technology-function', 'technology-process', 'technology-interaction', 'technology-event', 'technology-service', 'artifact',
                   'equipment', 'facility', 'distribution-network', 'material'],
    'motivation': ['stakeholder', 'driver', 'assessment', 'goal', 'outcome', 'principle', 'requirement', 'constraint', 'meaning', 'value'],
    'implementation': ['work-package', 'deliverable', 'implementation-event', 'plateau', 'gap'],
    'other': ['grouping', 'location', 'junction'],
}
ELEMENT_TYPES = {t: layer for layer, ts in ARCHIMATE_LAYERS.items() for t in ts}
RELATIONSHIP_TYPES = {'access', 'aggregation', 'assignment', 'association', 'composition', 'flow', 'influence', 'realization', 'serving',
                      'specialization', 'triggering'}
SECOND_ENGINES = re.compile(r'(?<![A-Za-z])(?:mermaid|cytoscape|joint(?:js)?\b|jointjs|dagre|elk(?:js|\.bundled)?|gojs|go\.js|konva|fabric(?:\.js)?|vis-network|visjs|vis\.js|'
                            r'reactflow|react-flow|xyflow|drawio|mxgraph|mxclient|bpmn-js|bpmn\.io|diagram-js|svg-pan-zoom|panzoom|jsplumb|sigma(?:\.js)?|'
                            r'leader-line|plantuml|viz(?:\.js)?\b|d3-force|zoomable|excalidraw|tldraw)(?![a-z])', re.I)
SECOND_ENGINE_MARKUP = re.compile(r'^(?:mermaid|cytoscape|react-flow\S*|joint-paper\S*|vis-network|jtk-\S+|jsplumb\S*|bpmn-\S+|djs-\S+|panzoom\S*|svg-pan-zoom\S*|mxgraph|diagram-canvas|node-link)$', re.I)
LIBRARY_SCRIPT = re.compile(r'(?:^|/)flask-basecoat(?:\.min)?\.js(?:\?|$)')
PAN_ZOOM_ATTRS = ('data-panzoom', 'data-pan-zoom', 'data-zoom', 'data-pan')


def check_one_diagram_engine(doc):
    """R15: a diagram region has the engine's root data-slot and its elements are drawn by the notation macros. The page
    carries no other engine's script and no diagram markup of any other kind. Runs on every page."""
    out = []
    for s in doc.xpath('//script'):
        src = s.get('src') or ''
        if src:
            if SECOND_ENGINES.search(src):
                out.append(f'a second diagram engine\'s script: {src}')
        elif (s.get('type') or '') not in ('application/json', 'application/ld+json') and SECOND_ENGINES.search(s.text or ''):
            out.append(f'an inline script that drives a second diagram engine ("{SECOND_ENGINES.search(s.text).group(0)}")')
    for el in elements(doc.xpath('//body')[0]):
        if in_template(el):
            continue
        for c in classes(el):
            if SECOND_ENGINE_MARKUP.match(c):
                out.append(f'markup of another diagram engine: class "{c}" on {describe(el)}')
    inside_engine = lambda e: any(a.get('data-slot') == 'diagram' for a in e.iterancestors())  # noqa: E731
    for el in elements(doc.xpath('//body')[0]):
        if in_template(el) or (el.get('data-slot') or '') == 'diagram' or inside_engine(el):
            continue
        # edges and nodes drawn by hand: an arrowed line, or an svg group of the usual node/edge classes, outside the engine
        if el.tag in ('line', 'path', 'polyline') and (el.get('marker-end') or el.get('marker-start')):
            out.append(f'a diagram edge drawn outside the diagram engine: {describe(el)}')
        if any(a in el.attrib for a in PAN_ZOOM_ATTRS):
            out.append(f'a pan-and-zoom surface outside the diagram engine: {describe(el)}')
        if any(re.search(r'pan-?zoom', c, re.I) for c in classes(el)):
            out.append(f'a pan-and-zoom surface outside the diagram engine: {describe(el)}')
    return out


def check_diagram(doc, region):
    out = []
    engines = region.xpath('.//*[@data-slot="diagram"]') + ([region] if region.get('data-slot') == 'diagram' else [])
    if len(engines) != 1:
        out.append(f'the diagram region has {len(engines)} elements with the engine\'s root data-slot="diagram"; it needs exactly one (R15)')
        return out
    root = engines[0]
    svgs = root.xpath('.//svg')
    if len([s for s in svgs if not s.xpath('ancestor::svg')]) != 1:
        out.append('the diagram is one SVG root')
    else:
        svg = svgs[0]
        if svg.get('role') != 'img' or not (svg.get('aria-label') or svg.get('aria-labelledby')):
            out.append('the SVG root needs role="img" and a name (CAN-1)')
    drawn = root.xpath('.//*[local-name()="rect" or local-name()="ellipse" or local-name()="polygon" or local-name()="circle" or local-name()="line" or local-name()="polyline" or local-name()="path"]')
    macro = '[@data-slot="diagram-element" or @data-slot="diagram-relationship" or @data-slot="diagram-notation"]'
    for d in drawn:
        if not d.xpath(f'ancestor::*{macro}') and not d.xpath('ancestor::*[local-name()="defs" or local-name()="marker"]'):
            out.append(f'a shape drawn outside the notation macros: {describe(d)}')
    nodes = root.xpath('.//*[@data-slot="diagram-element"]')
    for n in nodes:
        t = n.get('data-element-type')
        if t not in ELEMENT_TYPES:
            out.append(f'element type {t!r} is not an ArchiMate 3.2 element type: {describe(n)}')
        if not any(all_text(x).strip() for x in n.xpath('.//*[local-name()="text"]')):
            out.append(f'element has no text label node: {describe(n)}')
        layer = ELEMENT_TYPES.get(t)
        for e in [n] + list(n.iterdescendants()):
            for c in classes(e):
                m = COLOUR_UTIL_RE.match(strip_variant(c))
                if not m:
                    continue
                name = m.group('name')
                if NOTATION_TOKEN_RE.match(name):
                    if name.startswith('layer-') and layer and layer != 'other' and name.split('-')[1] != layer:
                        out.append(f'{t} is a {layer}-layer element but is coloured {name}: {describe(e)}')
                elif name not in THEME_TOKENS and not re.match(r'^(?:\d+|xs|sm|md|lg|xl|none|px)$', name):
                    out.append(f'colour "{c}" is neither a theme token nor a notation token: {describe(e)}')
    for r in root.xpath('.//*[@data-slot="diagram-relationship"]'):
        t = r.get('data-relationship-type')
        if t not in RELATIONSHIP_TYPES:
            out.append(f'relationship type {t!r} is not an ArchiMate 3.2 relationship type: {describe(r)}')
    for e in elements(root) + [root]:
        for c in classes(e):
            m = COLOUR_UTIL_RE.match(strip_variant(c))
            if m and e.xpath('ancestor-or-self::*[@data-slot="diagram-element"]'):
                continue
            if m and not (NOTATION_TOKEN_RE.match(m.group('name')) or m.group('name') in THEME_TOKENS or re.match(r'^(?:\d+|xs|sm|md|lg|xl|none|px)$', m.group('name'))):
                out.append(f'colour "{c}" is neither a theme token nor a notation token: {describe(e)}')
    # the list alternative: a table or an item group with one row per element (CAN-2)
    count = len(nodes)
    lists = [t for t in doc.xpath('//table[@data-slot="table"] | //table') if t.xpath('./caption | @aria-label')]
    rows = [len(t.xpath('./tbody/tr')) for t in lists] + [len(g.xpath('./*[@data-slot="item"]')) for g in doc.xpath('//*[@data-slot="item-group"]')]
    if count and count not in rows:
        out.append(f'no list alternative with {count} rows (a named Table or an ItemGroup, one row per element; found {rows or "none"}) (CAN-2)')
    if not count:
        out.append('the diagram has no elements drawn by the notation macros')
    return out


# ---- C3 timeline

NUM_RE = re.compile(r'^\s*-?\d+(?:\.\d+)?(?:%|px|rem|em|fr|ch)?\s*$|^\s*calc\(.*\)\s*$|^\s*var\(--[\w-]+\)\s*$')
PROP_RE = re.compile(r'(--[\w-]+)\s*:\s*([^;]+)')


def check_timeline(doc, region):
    out = []
    axis = region.xpath('.//*[@data-slot="timeline-axis"]')
    if not axis:
        out.append('no time axis (data-slot="timeline-axis")')
    else:
        ticks = [t for t in axis[0].xpath('.//*[@data-slot="timeline-tick"]') if all_text(t).strip()]
        if len(ticks) < 2:
            out.append(f'the time axis has {len(ticks)} labelled ticks; it needs at least 2')
        if not (axis[0].get('aria-label') or axis[0].get('aria-labelledby') or all_text(axis[0]).strip()):
            out.append('the time axis is not labelled')
    bars = region.xpath('.//*[@data-slot="timeline-bar"]')
    if not bars:
        out.append('no bars (data-slot="timeline-bar")')
    rows = region.xpath('.//*[@data-slot="timeline-row"]')
    if bars and rows and len(rows) < len(bars) and not any(len(r.xpath('.//*[@data-slot="timeline-bar"]')) > 1 for r in rows):
        out.append(f'{len(bars)} bars in {len(rows)} rows: one row per item')
    for b in bars:
        props = dict(PROP_RE.findall(b.get('style') or ''))
        for p in ('--x', '--w'):
            if p not in props:
                out.append(f'bar position must use {p}: {describe(b)}')
            elif not NUM_RE.match(props[p]):
                out.append(f'bar {p} value {props[p].strip()!r} is not a number, length or percentage: {describe(b)}')
        for c in classes(b):
            if re.match(r'^(?:[\w@\[\]/-]+:)*(?:left|right|ml|mr|w|translate-x|inset-x|start|end)-\[', c):
                out.append(f'bar is positioned by the arbitrary class "{c}", not --x and --w: {describe(b)}')
        if not all_text(b).strip() and not b.get('aria-label'):
            out.append(f'bar has no name: {describe(b)}')
    today = region.xpath('.//*[@data-slot="timeline-today"]')
    if not today or not all_text(today[0]).strip():
        out.append('no today marker with its text (TML-4)')
    tables = [t for t in doc.xpath('//table') if table_name(t)]
    if bars and not any(len(t.xpath('./tbody/tr')) == len(bars) for t in tables):
        out.append(f'no List view table with {len(bars)} rows, one per bar (TML-2)')
    else:
        text = ' '.join(all_text(t) for t in tables)
        for b in bars:
            for k in ('data-start', 'data-end'):
                if b.get(k) and b.get(k) not in text:
                    out.append(f'{k}={b.get(k)} of {describe(b)} is not in the List view (TML-3)')
    return out


# ---- C5 document

ANSWER_RE = re.compile(r'summary|answer|recommendation|decision|conclusion|key findings|at a glance|in brief|tl;dr|bottom line|overview', re.I)
NUMBERED_RE = re.compile(r'^\s*(\d+(?:\.\d+)*)[.)]?\s+\S')


def check_document(doc, region):
    out = []
    heads = [h for h in region.xpath('.//h1 | .//h2 | .//h3 | .//h4 | .//h5 | .//h6')]
    page_heads = doc.xpath('//h1 | //h2 | //h3 | //h4 | //h5 | //h6')
    scope = heads if heads else page_heads
    if len(doc.xpath('//h1')) != 1:
        out.append(f'{len(doc.xpath("//h1"))} <h1> elements; a document has one title (DOC-1)')
    prev = 0
    for h in scope:
        level = int(h.tag[1])
        if prev and level > prev + 1:
            out.append(f'heading order skips a level: <{h.tag}> "{all_text(h)[:40]}" follows <h{prev}>')
        prev = level
    # numbered headings run without gaps
    counters = {}
    for h in scope:
        m = NUMBERED_RE.match(all_text(h))
        if not m:
            continue
        parts = [int(x) for x in m.group(1).split('.')]
        depth = len(parts)
        if depth == 1:
            expect = counters.get((), 0) + 1
            counters = {(): parts[0]}
        else:
            key = tuple(parts[:-1])
            expect = counters.get(key, 0) + 1
            counters = {k: v for k, v in counters.items() if len(k) <= depth - 1}
            counters[key] = parts[-1]
        if parts[-1] != expect:
            out.append(f'numbered headings have a gap: "{all_text(h)[:40]}" (expected {".".join(map(str, parts[:-1] + [expect]))})')
    # answer first: the first section after the title is the summary or the answer
    h1 = (region.xpath('.//h1') or doc.xpath('//h1') or [None])[0]
    sections = [h for h in scope if h.tag in ('h2',)]
    marked = region.xpath('.//*[@data-answer-first]')
    if not marked:
        if not sections:
            out.append('no section headings: the first section must be the summary or the answer')
        elif not ANSWER_RE.search(all_text(sections[0])):
            out.append(f'the first section "{all_text(sections[0])[:40]}" is not the summary or the answer (answer first)')
        elif h1 is not None:
            # nothing substantial may come between the title and the answer
            for sib in h1.itersiblings():
                if sib is sections[0] or sib.xpath('.//h2[1]') and sections[0] in sib.iterdescendants():
                    break
                if isinstance(sib.tag, str) and sib.tag in ('table', 'figure', 'ul', 'ol', 'section') and all_text(sib).strip():
                    out.append(f'content comes before the answer: {describe(sib)}')
                    break
    return out


FORM_CHECKS = {'c1': lambda doc, r: check_diagram(doc, r), 'c2': lambda doc, r: check_heat_map(doc, r), 'c3': lambda doc, r: check_timeline(doc, r),
               'c4': lambda doc, r: check_canvas(r), 'c5': lambda doc, r: check_document(doc, r)}


def check_forms(doc, force=None):
    """Every marked region against its form's gate; R15 on every page."""
    out, found = [], []
    for form, raw, region in form_regions(doc):
        if form is None:
            out.append(f'data-entelim-form="{raw}" is not a Tier C form (c1 diagram, c2 heat map, c3 timeline, c4 canvas, c5 document)')
            continue
        found.append(form)
        for line in shared_form_checks(region, form) + FORM_CHECKS[form](doc, region):
            out.append(f'[{form.upper()}] {line}')
    if force and force not in found:
        out.append(f'[{force.upper()}] the page has no region marked data-entelim-form="{force}"')
    for line in check_one_diagram_engine(doc):
        out.append(f'[C1/R15] {line}')
    return out, found


# ================================================================ dispatch

def run_gates(selected, doc, text, *, target, nearest, original_doc, content_roots, golden_rel, tier='B', departures=(), force_form=None,
              pixel_region=None, rendered=False):
    """selected: subset of {'structure', 'pixels', 'charts', 'a11y', 'forms', 'help'}. Returns ({name: [failures]}, info)."""
    res, info = {}, {}
    if 'structure' in selected:
        res['A2 structure'], info['structure'] = check_structure(doc, original_doc, content_roots, tier)
    if 'charts' in selected:
        res['B9 charts'], info['charts'] = check_charts_static(doc)
    if 'forms' in selected:
        res['C forms'], info['forms'] = check_forms(doc, force_form)
    if 'help' in selected:
        for k, v in check_help_text(doc).items():
            res[f'help {k}'] = v
    if selected & {'pixels', 'a11y'} or ('charts' in selected and rendered):
        with page_urls(target, text, nearest, golden_rel) as (page_url, golden_url):
            if 'charts' in selected and rendered:
                res['B9 charts'] += check_charts_rendered(page_url)
            if 'pixels' in selected:
                res['A5 pixels'], info['pixels'] = check_pixels(page_url, golden_url, tier, pixel_region)
            if 'a11y' in selected:
                res['R9 a11y'], info['a11y'] = check_a11y_strict(page_url, golden_url, list(departures))
    return res, info
