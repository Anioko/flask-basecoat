"""Page check: does a page built with Flask-Basecoat stay inside shadcn/ui?

Use it on any page an application builds (not only the library's own reference pages). It answers one question with
numbers: is every visible part of this page a shadcn component carrying its exact recipe, laid out only with layout
and type utilities, coloured only with theme tokens, inside the frame of a named shadcn original, within the
density of that original?

    python compliance/scripts/check_page.py /examples/reference/portfolio --nearest dashboard-01
    python compliance/scripts/check_page.py page.html --nearest dashboard-01 --browser --json out.json

The target is a path served by the bare test app (flask_basecoat.testing.make_app plus the examples blueprint), a
full http(s) URL, or an HTML file. The page may also name its original in a comment:
`{# shadcn-nearest: dashboard-01 #}` renders nothing, so the check also accepts `<meta name="shadcn-nearest">`.

Checks (each prints PASS/FAIL with the offending nodes):
  components   every element with a data-slot is a pinned shadcn part (or a chart part); raw controls are refused
  recipes      every class on a component is from that component's recipe, from a recipe it is composed with
               (asChild), from the layout/type allowlist, or used at page level by the named original
  wrappers     every other element is a layout wrapper or text element with allowlisted classes only
  colours      colour utilities name theme tokens only; no hex/rgb/hsl/oklch literals in classes or styles
  styles       inline style holds only custom properties, except the inline styles the component macros emit
  structure    no card inside a card; one chart per chart card
  density      regions under the header <= the original's (6 for dashboard-01); stat row <= 4 cards of one shape;
               <= 2 chart cards; <= 1 primary table
  frame        the frame (sidebar, inset, site header and their parts) has the same part signature as the original's
  form         (Tier C pages, criteria-v3 1.5) one element marked data-entelim-form is a focusable named scroll region
               that keeps its natural width, carries geometry only as --x/--y/--w/--h/--col/--row custom properties,
               and the page offers the accessible alternative (a "... view" ToggleGroup and a Table). The marked
               region counts as one region in the density check; everything outside it is held to Tier B.
  browser      (--browser) every computed colour is a token value or an alpha of one, in light and dark; no
               horizontal overflow at 390px; no accessibility finding beyond those of the original

The fidelity score is the share of nodes in the content area that pass; a page is "shadcn composed" only at 100%.
"""
import json
import pathlib
import re
import sys

from lxml import html as lxml_html

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance' / 'golden' / 'out'
RECIPES = json.loads((ROOT / 'flask_basecoat' / 'data' / 'recipes.json').read_text(encoding='utf8'))

# ---------------------------------------------------------------- vocabularies

TOKENS = ['background', 'foreground', 'card', 'card-foreground', 'popover', 'popover-foreground', 'primary',
          'primary-foreground', 'secondary', 'secondary-foreground', 'muted', 'muted-foreground', 'accent',
          'accent-foreground', 'destructive', 'destructive-foreground', 'border', 'input', 'ring', 'chart-1', 'chart-2',
          'chart-3', 'chart-4', 'chart-5', 'sidebar', 'sidebar-foreground', 'sidebar-primary',
          'sidebar-primary-foreground', 'sidebar-accent', 'sidebar-accent-foreground', 'sidebar-border', 'sidebar-ring',
          'transparent', 'current', 'inherit']
COLOUR_PREFIX = r'(?:bg|text|border(?:-[trblxy])?|ring|ring-offset|outline|fill|stroke|from|via|to|divide|decoration|accent|caret|placeholder|shadow)'
COLOUR_UTILITY = re.compile(rf'^{COLOUR_PREFIX}-([a-z]+(?:-[a-z0-9]+)*?)(?:/\d+)?$')
NON_COLOUR_SUFFIX = re.compile(r'^(?:xs|sm|base|md|lg|xl|\dxl|left|right|center|justify|start|end|wrap|nowrap|balance|pretty|clip|ellipsis|'
                               r'\d+|px|0|none|solid|dashed|dotted|double|hidden|x|y|t|b|l|r|s|e|inset|opacity-\d+|'
                               r'collapse|separate|fixed|local|scroll|auto|cover|contain|repeat|no-repeat|center|top|bottom|'
                               r'gradient-to-[a-z]+|linear-to-[a-z]+|offset-\d+|clip-[a-z]+|origin-[a-z]+|blend-[a-z]+)$')
RAW_COLOUR_LITERAL = re.compile(r'#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\boklch\(|\boklab\(|\blab\(|\blch\(')

# Layout, spacing, sizing and type utilities a wrapper or text element may carry (Tier B rules 3 and 4).
LAYOUT = [
    r'flex', r'inline-flex', r'grid', r'inline-grid', r'block', r'inline-block', r'inline', r'contents', r'hidden', r'sr-only', r'not-sr-only',
    r'flex-(?:1|auto|initial|none|row|col|row-reverse|col-reverse|wrap|nowrap)', r'(?:grow|shrink)(?:-0)?', r'basis-\S+', r'order-\S+',
    r'grid-cols-\S+', r'grid-rows-\S+', r'col-(?:span|start|end)-\S+', r'row-(?:span|start|end)-\S+', r'auto-(?:cols|rows)-\S+', r'grid-flow-\S+',
    r'gap(?:-[xy])?-\S+', r'space-[xy]-\S+',
    r'-?[pm][trblxyse]?-\S+', r'-?inset(?:-[xy])?-\S+', r'-?(?:top|right|bottom|left|start|end)-\S+',
    r'(?:min-|max-)?[wh]-\S+', r'size-\S+', r'aspect-\S+',
    r'(?:items|justify|self|content|place-items|place-content|place-self|justify-items|justify-self)-\S+',
    r'overflow(?:-[xy])?-\S+', r'overscroll(?:-[xy])?-\S+', r'scroll-\S+', r'snap-\S+', r'truncate', r'line-clamp-\S+',
    r'relative', r'absolute', r'sticky', r'static', r'z-\S+', r'isolate',
    r'@container(?:/\S+)?', r'container',
    r'text-(?:xs|sm|base|lg|xl|[2-9]xl)', r'text-(?:left|center|right|start|end|balance|pretty|wrap|nowrap)',
    r'font-(?:normal|medium|semibold|bold|mono|sans)', r'tabular-nums', r'leading-\S+', r'tracking-(?:tight|tighter|normal|wide)',
    r'whitespace-\S+', r'break-\S+', r'italic', r'not-italic', r'underline', r'no-underline', r'underline-offset-\S+', r'uppercase', r'lowercase', r'capitalize', r'normal-case',
    r'list-(?:disc|decimal|none|inside|outside)', r'select-none', r'pointer-events-none', r'cursor-\S+',
    r'rounded(?:-[a-z]+)?', r'border(?:-[trblxy])?(?:-\d)?', r'border-dashed', r'divide-[xy](?:-\d)?',
    r'opacity-\d+', r'transition(?:-\S+)?', r'duration-\d+', r'ease-\S+', r'animate-(?:spin|pulse)',
    r'lucide', r'lucide-[a-z0-9-]+', r'cn-rtl-flip', r'tw-\S+',
    r'group(?:/\S+)?', r'peer(?:/\S+)?',
]
LAYOUT_RE = re.compile('^(?:' + '|'.join(LAYOUT) + ')$')
VARIANT_PREFIX = re.compile(r'^(?:(?:sm|md|lg|xl|2xl|max-sm|max-md|max-lg|@[a-z0-9]+(?:/[a-z]+)?|@\[[^\]]+\](?:/[a-z]+)?|dark|hover|focus|focus-visible|'
                            r'first|last|odd|even|empty|disabled|group-[a-z-]+(?:/[a-z-]+)?|peer-[a-z-]+(?:/[a-z-]+)?|data-[a-z-]+(?:=[^:]+)?|'
                            r'\*|has-\[[^\]]+\]|in-[a-z-]+|aria-[a-z-]+|rtl|ltr|print|motion-[a-z]+):)+')

WRAPPER_TAGS = {'div', 'section', 'main', 'header', 'footer', 'nav', 'aside', 'article', 'form', 'ul', 'ol', 'li', 'span', 'p',
                'h1', 'h2', 'h3', 'h4', 'a', 'strong', 'em', 'b', 'i', 'small', 'code', 'time', 'abbr', 'br', 'dl', 'dt', 'dd',
                'figure', 'figcaption', 'blockquote', 'pre', 'template', 'svg', 'path', 'circle', 'rect', 'line', 'polyline',
                'polygon', 'g', 'ellipse', 'defs', 'linearGradient', 'stop', 'text', 'tspan', 'title', 'clipPath', 'mask',
                'img', 'label', 'fieldset', 'legend', 'input', 'select', 'option', 'button', 'textarea', 'table', 'thead',
                'tbody', 'tr', 'th', 'td', 'caption', 'colgroup', 'col', 'kbd', 'mark', 'sup', 'sub', 'hr',
                'link', 'meta'}  # React emits <link rel=preload> for images inside the body
CONTROL_TAGS = {'button', 'input', 'select', 'textarea', 'table'}

# Inline styles the component macros and runtime emit on their own parts (not authored by the page).
MACRO_STYLE_SLOTS = {'progress-indicator', 'sidebar-wrapper', 'resizable-panel-group', 'resizable-panel', 'resizable-handle',
                     'scroll-area-viewport', 'select-value', 'chart', 'slider-range', 'slider-thumb', 'carousel-content',
                     'tooltip-content', 'popover-content', 'dropdown-menu-content', 'select-content', 'hover-card-content',
                     'chart-legend-content', 'chart-tooltip-content'}
CUSTOM_PROPERTIES_ONLY = re.compile(r'^\s*(?:--[a-zA-Z0-9-]+\s*:[^;]+;?\s*)*$')

# Recharts' own SVG classes inside a chart container.
RECHARTS = re.compile(r'^(?:recharts-\S+|xAxis|yAxis|angleAxis|radiusAxis)$')


def strip_variant(c):
    c = c.lstrip('!')
    c = VARIANT_PREFIX.sub('', c)
    return c[:-1] if c.endswith('!') else c


def recipe_vocab():
    """slot -> set of every class its recipe can emit (base, cva base, every option, alternates, CONST)."""
    from flask_basecoat import slots
    vocab, markers = {}, {}
    for name, rec in RECIPES.items():
        words = set(rec.get('base_classes', '').split())
        cva = rec.get('variants') or {}
        words |= set(cva.get('base', '').split())
        for options in cva.get('variants', {}).values():
            for cls in options.values():
                words |= set(cls.split())
        for alt in (rec.get('alts') or {}).values() if isinstance(rec.get('alts'), dict) else (rec.get('alts') or []):
            words |= set((alt.get('base_classes', '') if isinstance(alt, dict) else str(alt)).split())
        const = getattr(slots, 'CONST', {}).get(name)
        if isinstance(const, dict):
            words |= set(str(const.get('class', '')).split())
        vocab[name] = words
        for w in words:
            if w.startswith('cn-') and w.count('-') >= 1 and not any(w.endswith(s) for s in ('-default', '-sm', '-lg', '-xs')):
                markers.setdefault(w, set()).add(name)
    return vocab, markers


VOCAB, MARKERS = recipe_vocab()
ALLOWED_SLOTS = set(RECIPES) | {'chart-style', 'example', 'example-wrapper', 'example-content'}


# ---------------------------------------------------------------- loading

def load(target):
    if target.startswith(('http://', 'https://')):
        import urllib.request
        return urllib.request.urlopen(target).read().decode('utf8'), target
    p = pathlib.Path(target)
    if p.suffix == '.html' and p.exists():
        return p.read_text(encoding='utf8'), str(p)
    from flask_basecoat.testing import make_app
    app = make_app()
    if 'basecoat_examples' not in app.blueprints:
        from flask_basecoat.examples import examples_bp
        app.register_blueprint(examples_bp, url_prefix='/examples')
    with app.test_client() as c:
        r = c.get(target, follow_redirects=True)
        if r.status_code != 200:
            raise SystemExit(f'{target}: HTTP {r.status_code}')
        return r.get_data(as_text=True), target


def golden_path(nearest):
    for p in (GOLDEN / 'blocks' / f'{nearest}.html', GOLDEN / f'{nearest}.html', GOLDEN / 'charts' / f'{nearest}.html'):
        if p.exists():
            return p
    return None


def original_classes(doc):
    """Every class the original uses on elements that are not components (its page-level styling)."""
    out = set()
    for el in doc.iter():
        if isinstance(el.tag, str):
            out |= set((el.get('class') or '').split())
    return out


def style_signature(style):
    """The set of property names in an inline style (values vary with data; the properties are the component's)."""
    return tuple(sorted({d.split(':', 1)[0].strip().lower() for d in style.split(';') if ':' in d}))


def original_styles(doc):
    return {style_signature(el.get('style')) for el in doc.iter() if isinstance(el.tag, str) and el.get('style')}


def closed_floating(el):
    """Closed menus, popovers and dialogs: React renders them only while open, so they are not part of the frame."""
    for a in [el] + list(el.iterancestors()):
        if not isinstance(a.tag, str):
            continue
        s = a.get('data-slot') or ''
        if a.get('data-state') == 'closed' and s.endswith(('-content', '-overlay', '-portal')):
            return True
    return False


def nearest_from_page(doc):
    for m in doc.xpath('//meta[@name="shadcn-nearest"]'):
        return m.get('content')
    return None


# ---------------------------------------------------------------- checks

def describe(el):
    s = el.get('data-slot')
    cls = (el.get('class') or '')[:80]
    return f"<{el.tag}{' data-slot=' + s if s else ''} class=\"{cls}\">"


def in_component(el):
    p = el.getparent()
    while p is not None:
        if isinstance(p.tag, str) and p.get('data-slot'):
            return p
        p = p.getparent()
    return None


def content_roots(doc):
    """The content area: everything in the sidebar inset except its site header; else <main>; else <body>."""
    inset = doc.xpath('//*[@data-slot="sidebar-inset"]')
    if inset:
        return [c for c in inset[0] if isinstance(c.tag, str) and c.tag != 'header'] or [inset[0]]
    mains = doc.xpath('//main')
    return [mains[0]] if mains else [doc.xpath('//body')[0]]


def in_roots(el, roots):
    return any(el is r or r in el.iterancestors() for r in roots)


# Components whose upstream markup itself contains native controls (react-day-picker's day buttons and month/year
# selects, input-otp's input, Radix's hidden select, embla's buttons, cmdk's input).
NATIVE_HOSTS = {'calendar', 'input-otp', 'native-select', 'native-select-wrapper', 'select', 'combobox', 'command', 'carousel', 'slider'}


def companion_control(el, orig_styles):
    """A native control a component renders for forms (hidden bubble input, hidden select): aria-hidden, type
    hidden, or carrying an inline style the original's components also carry."""
    if el.get('type') == 'hidden' or el.get('aria-hidden') == 'true':
        return True
    if any(isinstance(x.tag, str) and x.get('data-slot') in NATIVE_HOSTS for x in el.iterancestors()):
        return True
    return bool(el.get('style')) and style_signature(el.get('style')) in orig_styles and in_component(el) is not None


FORM_CUSTOM_PROPERTIES = {'--x', '--y', '--w', '--h', '--col', '--row'}
FORMS = {'C1', 'C2', 'C3', 'C4', 'C5'}


def check_form(doc, marked):
    """Tier C shared conditions (criteria-v3 1.5, accessibility-v1 section 2): one marked region, a focusable named
    horizontal scroll region, geometry only through the sanctioned custom properties, and the accessible alternative."""
    if not marked:
        return []
    out = []
    if len(marked) > 1:
        out.append(f'{len(marked)} regions are marked data-entelim-form; a page has one')
    m = marked[0]
    if m.get('data-entelim-form') not in FORMS:
        out.append(f'data-entelim-form="{m.get("data-entelim-form")}" is not one of {sorted(FORMS)}')
    if m.get('role') != 'region' or not (m.get('aria-label') or m.get('aria-labelledby')):
        out.append('the marked region is not role="region" with an accessible name')
    if m.get('tabindex') != '0':
        out.append('the marked region is not focusable (tabindex="0"), so a keyboard user cannot scroll it')
    if 'overflow-x-auto' not in (m.get('class') or '').split():
        out.append('the marked region does not scroll horizontally (overflow-x-auto) on a phone')
    for el in m.iter():
        if isinstance(el.tag, str) and el.get('style') and not el.xpath('ancestor-or-self::*[@data-slot="chart"]'):
            props = {d.split(':', 1)[0].strip() for d in el.get('style').split(';') if ':' in d}
            if props - FORM_CUSTOM_PROPERTIES and not (el.get('data-slot') in MACRO_STYLE_SLOTS):
                out.append(f'{describe(el)}: geometry style uses {sorted(props - FORM_CUSTOM_PROPERTIES)}; only --x --y --w --h --col --row are allowed')
    if not [g for g in doc.xpath('//*[@data-slot="toggle-group"]') if 'view' in (g.get('aria-label') or '').lower()]:
        out.append('no view switch: a ToggleGroup whose name ends in "view" must offer the list route')
    if not doc.xpath('//*[@data-slot="table"]'):
        out.append('no Table: the same data must be reachable as a real table')
    return out


def check(doc, original_doc, original_name, limits):
    res = {k: [] for k in ('components', 'recipes', 'wrappers', 'colours', 'styles', 'structure', 'density', 'frame', 'form')}
    orig_cls = original_classes(original_doc) if original_doc is not None else set()
    orig_styles = original_styles(original_doc) if original_doc is not None else set()
    body = doc.xpath('//body')[0]
    content = content_roots(doc)
    content_nodes, content_ok = 0, 0

    for el in body.iter():
        if not isinstance(el.tag, str) or el.tag in ('script', 'style', 'template', 'noscript'):
            continue
        if el is body or any(a.tag in ('template', 'script', 'style') for a in el.iterancestors() if isinstance(a.tag, str)):
            continue
        slot = el.get('data-slot')
        classes = (el.get('class') or '').split()
        inside_chart = any((a.get('data-slot') == 'chart') for a in el.iterancestors() if isinstance(a.tag, str))
        in_content = in_roots(el, content)
        problems = []

        if slot:
            if slot not in ALLOWED_SLOTS:
                res['components'].append(f'unknown part {describe(el)}')
                problems.append('component')
            vocab = set(VOCAB.get(slot, set()))
            for c in classes:
                for rec in MARKERS.get(c, ()):  # composed recipes (asChild: a button rendered as a sidebar button ...)
                    vocab |= VOCAB.get(rec, set())
            for c in classes:
                if c in vocab or c in orig_cls or LAYOUT_RE.match(strip_variant(c)) or RECHARTS.match(c):
                    continue
                if COLOUR_UTILITY.match(strip_variant(c)):
                    continue  # judged by the colour check
                res['recipes'].append(f'{describe(el)}: class "{c}" is not in its recipe or the layout allowlist')
                problems.append('recipe')
        elif not inside_chart:
            if el.tag in CONTROL_TAGS and not companion_control(el, orig_styles):
                res['components'].append(f'raw control {describe(el)}')
                problems.append('control')
            if el.tag not in WRAPPER_TAGS:
                res['wrappers'].append(f'element <{el.tag}> is not a wrapper or text element')
                problems.append('wrapper')
            for c in classes:
                if c in orig_cls or LAYOUT_RE.match(strip_variant(c)) or COLOUR_UTILITY.match(strip_variant(c)) or RECHARTS.match(c):
                    continue
                res['wrappers'].append(f'{describe(el)}: class "{c}" is not layout or type')
                problems.append('wrapper')

        for c in classes:
            base = strip_variant(c)
            m = COLOUR_UTILITY.match(base)
            if m and not NON_COLOUR_SUFFIX.match(m.group(1)) and m.group(1) not in TOKENS and c not in orig_cls and c not in VOCAB.get(slot or '', ()):
                if not (m.group(1) in ('white', 'black') and c in orig_cls):
                    res['colours'].append(f'{describe(el)}: "{c}" is not a theme token')
                    problems.append('colour')
            if RAW_COLOUR_LITERAL.search(c) and c not in orig_cls and c not in VOCAB.get(slot or '', ()):
                res['colours'].append(f'{describe(el)}: raw colour in class "{c}"')
                problems.append('colour')

        style = el.get('style')
        if style and not inside_chart:
            component_output = slot in MACRO_STYLE_SLOTS or (bool(slot) or in_component(el) is not None) and style_signature(style) in orig_styles
            if not (component_output or CUSTOM_PROPERTIES_ONLY.match(style)):
                res['styles'].append(f'{describe(el)}: inline style "{style[:80]}"')
                problems.append('style')
            if RAW_COLOUR_LITERAL.search(style):
                res['colours'].append(f'{describe(el)}: raw colour in style "{style[:80]}"')
                problems.append('colour')

        if in_content:
            content_nodes += 1
            content_ok += 0 if problems else 1

    # structure: card in card, charts per card
    for card in doc.xpath('//*[@data-slot="card"]'):
        if card.xpath('ancestor::*[@data-slot="card"]'):
            res['structure'].append(f'card inside a card: {describe(card)}')
        n = len(card.xpath('.//*[@data-slot="chart"]'))
        if n > 1:
            res['structure'].append(f'{n} charts in one card: {describe(card)}')

    # density
    def within(xp):
        out = []
        for r in content:
            out += ([r] if r.xpath('self::*' + xp[len('.//*'):]) else []) + r.xpath(xp)
        return out
    marked = doc.xpath('//*[@data-entelim-form]')
    top_cards = [c for c in within('.//*[@data-slot="card"]') if not c.xpath('ancestor::*[@data-slot="card"]')
                 and not c.xpath('ancestor::*[@data-entelim-form]')]
    regions = len(top_cards) + (1 if marked and any(in_roots(m, content) for m in marked) else 0)
    chart_cards = [c for c in top_cards if c.xpath('.//*[@data-slot="chart"]')]
    table_cards = [c for c in top_cards if c.xpath('.//*[@data-slot="table"]')]
    loose_tables = [t for t in within('.//*[@data-slot="table"]') if not t.xpath('ancestor::*[@data-slot="card"]')]
    res['form'] += check_form(doc, marked)
    stat = [c for c in top_cards if c.xpath('./*[@data-slot="card-header"]/*[@data-slot="card-action"]') and not c.xpath('.//*[@data-slot="chart"] | .//*[@data-slot="table"]')]
    shapes = {tuple(x.get('data-slot') for x in c.iter() if isinstance(x.tag, str) and x.get('data-slot')) for c in stat}
    if regions > limits['regions']:
        res['density'].append(f'{regions} card regions; the original has at most {limits["regions"]}')
    if len(stat) > limits['stat_cards']:
        res['density'].append(f'{len(stat)} stat cards; at most {limits["stat_cards"]}')
    if len(shapes) > 1:
        res['density'].append(f'stat cards have {len(shapes)} different structures; use one')
    if len(chart_cards) > limits['charts']:
        res['density'].append(f'{len(chart_cards)} chart cards; at most {limits["charts"]}')
    if len(table_cards) + len(loose_tables) > limits['tables']:
        res['density'].append(f'{len(table_cards) + len(loose_tables)} tables; at most {limits["tables"]} primary table')

    # frame: the set of part paths outside the content area equals the original's
    if original_doc is not None:
        def frame_sig(d):
            croots = content_roots(d)
            sig = set()
            for el in d.xpath('//*[@data-slot]'):
                if in_roots(el, croots) or closed_floating(el):
                    continue
                path = [a.get('data-slot') for a in reversed(list(el.iterancestors())) if isinstance(a.tag, str) and a.get('data-slot')]
                sig.add('/'.join(path + [el.get('data-slot')]))
            return sig
        ours, theirs = frame_sig(doc), frame_sig(original_doc)
        missing, extra = sorted(theirs - ours), sorted(ours - theirs)
        for p in missing[:10]:
            res['frame'].append(f'frame part missing: {p}')
        for p in extra[:10]:
            res['frame'].append(f'frame part not in {original_name}: {p}')

    score = round(100 * content_ok / max(1, content_nodes), 2)
    return res, score, {'regions': regions, 'stat_cards': len(stat), 'chart_cards': len(chart_cards),
                        'tables': len(table_cards) + len(loose_tables), 'content_nodes': content_nodes}


COLLECT_JS = r"""() => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true });
  const rgb = (v) => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = v; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3]]; };
  const opaque = (v) => { const m = /\/\s*([\d.]+%?)\s*\)$/.exec(v) || /^rgba\([^)]*,\s*([\d.]+)\)$/.exec(v); return m ? v.replace(/\s*\/\s*[\d.]+%?\s*\)$/, ')').replace(/^rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)$/, 'rgb($1, $2, $3)') : v; };
  const alpha = (v) => { const m = /\/\s*([\d.]+)(%?)\s*\)$/.exec(v) || /^rgba\([^)]*,\s*([\d.]+)\)$/.exec(v); if (!m) return 1; return m[2] === '%' ? +m[1] / 100 : +m[1]; };
  const root = getComputedStyle(document.documentElement);
  const names = new Set([...document.styleSheets].flatMap(s => { try { return [...s.cssRules]; } catch (e) { return []; } }).flatMap(function walk(r) { return [...(r.style ? [...r.style].filter(n => n.startsWith('--')) : []), ...(r.cssRules ? [...r.cssRules].flatMap(walk) : [])]; }));
  const tokens = [[0, 0, 0], [255, 255, 255]];
  for (const n of names) { const v = root.getPropertyValue(n).trim(); if (/^(oklch|oklab|rgb|hsl|#|lab|lch|color)/.test(v)) { const c = rgb(opaque(v)); if (c[3] === 255) tokens.push(c.slice(0, 3)); } }
  const near = (c) => tokens.some(t => Math.abs(t[0] - c[0]) <= 3 && Math.abs(t[1] - c[1]) <= 3 && Math.abs(t[2] - c[2]) <= 3);
  const bad = new Set();
  // Recharts' own default paints (#666 tick labels, #ccc grid, #fff/#000 strokes) show in upstream's charts too:
  // in Recharts 3.8 the tick labels sit outside the .recharts-cartesian-axis-tick group shadcn's chart class targets.
  const RECHARTS_DEFAULTS = new Set(['102,102,102', '204,204,204', '255,255,255', '0,0,0']);
  for (const el of document.body.querySelectorAll('*')) {
    const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const inChart = !!el.closest('.recharts-wrapper');
    for (const prop of ['color', 'background-color', 'border-top-color', 'fill', 'stroke']) {
      const v = cs.getPropertyValue(prop); if (!v || v === 'none' || v.includes('url(') || alpha(v) === 0) continue;
      const c = rgb(opaque(v)); if (c[3] !== 255) continue;
      if (inChart && RECHARTS_DEFAULTS.has(c.slice(0, 3).join(','))) continue;
      if (!near(c.slice(0, 3))) bad.add(`rgb(${c[0]}, ${c[1]}, ${c[2]})|${el.tagName.toLowerCase()}${el.dataset.slot ? '[' + el.dataset.slot + ']' : ''} ${prop}`);
    }
  }
  return [...bad];
}"""


def browser_checks(target_url, html_text, original_url):
    """Computed colours are theme token values (or alphas of them) in light and dark, apart from colours the original
    itself uses; no horizontal overflow at 390px."""
    from playwright.sync_api import sync_playwright
    out = []

    def colours(pg, url, html, theme):
        if url:
            pg.goto(url + (('&' if '?' in url else '?') + f'theme={theme}'))
        else:
            pg.set_content(html)
        pg.evaluate(f"document.documentElement.classList.toggle('dark', {str(theme == 'dark').lower()})")
        pg.add_style_tag(content='*,*::before,*::after{transition:none!important;animation:none!important}')
        pg.wait_for_timeout(400)
        return pg.evaluate(COLLECT_JS)

    with sync_playwright() as p:
        b = p.chromium.launch()
        for theme in ('light', 'dark'):
            pg = b.new_page(viewport={'width': 1440, 'height': 900})
            ours = colours(pg, target_url, html_text, theme)
            theirs = {x.split('|')[0] for x in colours(pg, original_url, None, theme)} if original_url else set()
            for x in ours:
                value, where = x.split('|', 1)
                if value not in theirs:
                    out.append(f'[{theme}] off-token colour {value} on {where}')
            pg.close()
        pg = b.new_page(viewport={'width': 390, 'height': 844})
        if target_url:
            pg.goto(target_url)
        else:
            pg.set_content(html_text)
        pg.wait_for_timeout(300)
        over = pg.evaluate('() => document.documentElement.scrollWidth - window.innerWidth')
        if over > 1:
            out.append(f'[390px] page overflows horizontally by {over}px')
        b.close()
    return out[:40]


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    target = args[0]
    nearest = argv[argv.index('--nearest') + 1] if '--nearest' in argv else None
    text, where = load(target)
    doc = lxml_html.fromstring(text)
    nearest = nearest or nearest_from_page(doc)
    original_doc = None
    if nearest:
        gp = golden_path(nearest)
        if not gp:
            raise SystemExit(f'no golden render for {nearest} in compliance/golden/out')
        original_doc = lxml_html.fromstring(gp.read_text(encoding='utf8'))
    limits = {'regions': 6, 'stat_cards': 4, 'charts': 2, 'tables': 1}
    res, score, counts = check(doc, original_doc, nearest, limits)
    if '--browser' in argv:
        url = None
        if target.startswith(('http://', 'https://')):
            url = target
        original_url = None
        if url and nearest:
            from urllib.parse import urlsplit
            u = urlsplit(url)
            gp = golden_path(nearest).relative_to(GOLDEN).as_posix()
            original_url = f'{u.scheme}://{u.netloc}/basecoat/golden/{gp}'
        res['browser'] = browser_checks(url, text if not url else None, original_url)
    failed = [k for k, v in res.items() if v]
    marked = doc.xpath('//*[@data-entelim-form]')
    tier = f'Tier C ({marked[0].get("data-entelim-form")})' if marked else 'Tier B'
    print(f'{where}  nearest original: {nearest or "(none named)"}  {tier}')
    for k, v in res.items():
        print(f"{'PASS' if not v else 'FAIL'} {k}" + (f' ({len(v)})' if v else ''))
        for line in v[:12]:
            print('      ', line)
    print(f"counts: {counts}")
    print(f'content fidelity: {score}% of {counts["content_nodes"]} nodes')
    verdict = 'shadcn composed' if not failed and score == 100 else 'not shadcn composed'
    print(f'{verdict.upper()}')
    if '--json' in argv:
        pathlib.Path(argv[argv.index('--json') + 1]).write_text(json.dumps({'target': where, 'nearest': nearest, 'results': res,
                                                                           'score': score, 'counts': counts, 'verdict': verdict}, indent=2), encoding='utf8')
    return 0 if verdict == 'shadcn composed' else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
