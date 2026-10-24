"""Runtime check: every page loads without script errors and its interactive parts behave like Radix.

For each page the browser records page errors and console errors, then exercises what is present:
  dialogs, sheets, drawers, alert dialogs, popovers, dropdown/context menus, menubar menus, selects, comboboxes:
      open from the trigger (click / right-click / hover), content gets data-state="open", Escape closes it and
      focus returns to the trigger (menus, dialogs)
  tabs: ArrowRight moves the active tab; checkbox/switch/toggle: click flips aria-checked / aria-pressed;
  radio groups: click selects; accordion/collapsible: click expands and collapses; sliders: ArrowRight raises the value.
Charts (/basecoat/charts/<name> and the `chart` component example): every chart must be drawn
  (svg.recharts-surface with a size). For the 67 charts with a tooltip the pointer is moved to the point recorded in
  compliance/golden/out/charts/manifest.json and the whole chart wrapper (tooltip, cursor, active dots and shapes) is
  compared with <name>.hover.html (see chart_compare.py), tooltip position within 0.5px; when the pointer leaves the
  chart the tooltip must hide. Interactive charts: each control (select item, button) must redraw the chart.
Charts inside blocks (blocks/dashboard-01; browser goldens out/blocks/<name>.chart*.html, manifest key blocks/<name>):
  at the 1440x900 block viewport the drawn chart, the hover replay (pointer placed relative to the chart surface) and
  every range chosen with the ToggleGroup or the Select must match the golden of that range (see exercise_block_chart).
Usage: python compliance/scripts/check_runtime.py [name ...] [--json out.json]
"""
import json
import pathlib
import re
import sys
import threading

from werkzeug.serving import make_server

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GOLDEN = ROOT / 'compliance/golden/out'

OPEN_FAMILIES = {
    'dialog': 'click', 'alert-dialog': 'click', 'sheet': 'click', 'drawer': 'click', 'popover': 'click',
    'dropdown-menu': 'click', 'context-menu': 'contextmenu', 'menubar-menu': 'click', 'select': 'click',
    'tooltip': 'hover', 'hover-card': 'hover', 'combobox': 'click',
}


def exercise(page):
    """Run the interaction script in the page and return a list of problems."""
    return page.evaluate(r"""
    async (families) => {
      const problems = [];
      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
      const key = (el, k) => el.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true }));
      const esc = () => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
      for (const [kind, how] of Object.entries(families)) {
        const slot = kind === 'menubar-menu' ? 'menubar' : kind;
        const contents = Array.from(document.querySelectorAll(`[data-slot="${slot}-content"]`)).slice(0, 4);
        for (const content of contents) {
          let trigger = content.id && (document.querySelector(`[aria-controls="${content.id}"]:not([data-slot$="-content"])`) || document.querySelector(`[data-fb-open="${content.id}"]`));
          if (!trigger && kind === 'tooltip') trigger = document.querySelector(`[aria-describedby="${content.id}"]`);
          if (!trigger && (kind === 'hover-card' || kind === 'context-menu')) { const all = Array.from(document.querySelectorAll(`[data-slot="${slot}-trigger"]`)).filter((t) => t.compareDocumentPosition(content) & Node.DOCUMENT_POSITION_FOLLOWING); trigger = all[all.length - 1]; }
          if (!trigger) continue; // opened programmatically only
          if (trigger.closest('[data-state="closed"][data-slot$="-content"]')) continue; // lives inside another closed popup
          if (trigger.disabled) continue;
          trigger.scrollIntoView({ block: 'center' });
          if (how === 'click') trigger.click();
          else if (how === 'contextmenu') trigger.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: 200, clientY: 200 }));
          else { trigger.dispatchEvent(new PointerEvent('pointerenter', { bubbles: true })); trigger.focus(); }
          await sleep(how === 'hover' ? 900 : 60);
          if (content.getAttribute('data-state') !== 'open') { problems.push(`${kind}: did not open (${trigger.textContent.trim().slice(0, 30)})`); esc(); continue; }
          const cs = getComputedStyle(content);
          if (cs.display === 'none' || cs.visibility === 'hidden') problems.push(`${kind}: open but not displayed`);
          if (how === 'hover') { trigger.dispatchEvent(new PointerEvent('pointerleave', { bubbles: true })); trigger.blur(); await sleep(500); }
          else { for (let i = 0; i < 4 && content.getAttribute('data-state') === 'open'; i++) { esc(); await sleep(60); } } // inner layers close first, like Radix
          if (content.getAttribute('data-state') !== 'closed') problems.push(`${kind}: did not close`);
          if (how === 'click' && kind !== 'select' && kind !== 'combobox' && document.activeElement !== trigger && !['tooltip', 'hover-card', 'context-menu'].includes(kind)) problems.push(`${kind}: focus not returned to trigger`);
          await sleep(260);
        }
      }
      // tabs
      const hiddenIn = (el) => !!el.closest('[data-state="closed"][data-slot$="-content"], [data-state="inactive"][data-slot="tabs-content"], [hidden]');
      for (const tabs of Array.from(document.querySelectorAll('[data-slot="tabs"]')).filter((t) => !hiddenIn(t)).slice(0, 3)) {
        const triggers = Array.from(tabs.querySelectorAll('[data-slot="tabs-trigger"]'));
        if (triggers.length < 2) continue;
        triggers[0].focus(); key(triggers[0], 'ArrowRight'); await sleep(20);
        if (triggers[1].getAttribute('aria-selected') !== 'true' && triggers[1].getAttribute('data-state') !== 'active') problems.push('tabs: ArrowRight did not activate the next tab');
        triggers[0].click(); await sleep(20);
        if (triggers[0].getAttribute('data-state') !== 'active') problems.push('tabs: click did not activate');
      }
      for (const sel of ['[data-slot="checkbox"]', '[data-slot="switch"]']) {
        const el = Array.from(document.querySelectorAll(sel)).find((e) => !e.disabled && !hiddenIn(e));
        if (!el) continue;
        const before = el.getAttribute('aria-checked'); el.click(); await sleep(10);
        if (el.getAttribute('aria-checked') === before) problems.push(`${sel}: click did not toggle aria-checked`);
        el.click();
      }
      const toggle = Array.from(document.querySelectorAll('[data-slot="toggle"]')).find((e) => !e.disabled && !e.closest('[data-slot="toggle-group"]') && !hiddenIn(e));
      if (toggle) { const b = toggle.getAttribute('aria-pressed'); toggle.click(); await sleep(10); if (toggle.getAttribute('aria-pressed') === b) problems.push('toggle: click did not toggle aria-pressed'); toggle.click(); }
      const radio = Array.from(document.querySelectorAll('[data-slot="radio-group"]')).find((e) => !hiddenIn(e));
      if (radio) { const items = Array.from(radio.querySelectorAll('[data-slot="radio-group-item"]:not([disabled])')); if (items.length > 1) { items[1].click(); await sleep(10); if (items[1].getAttribute('aria-checked') !== 'true') problems.push('radio-group: click did not select'); } }
      const acc = Array.from(document.querySelectorAll('[data-slot="accordion-trigger"]')).find((e) => !hiddenIn(e));
      if (acc) { const before = acc.getAttribute('aria-expanded'); acc.click(); await sleep(10); if (acc.getAttribute('aria-expanded') === before) problems.push('accordion: click did not toggle'); acc.click(); await sleep(260); }
      const col = Array.from(document.querySelectorAll('[data-slot="collapsible-trigger"]')).find((e) => !hiddenIn(e));
      if (col) { const before = col.getAttribute('aria-expanded'); col.click(); await sleep(10); if (col.getAttribute('aria-expanded') === before) problems.push('collapsible: click did not toggle'); col.click(); await sleep(260); }
      const thumb = Array.from(document.querySelectorAll('[data-slot="slider-thumb"]')).find((t) => !t.closest('[data-slot="slider"][aria-disabled="true"]') && !hiddenIn(t));
      if (thumb) { const v = Number(thumb.getAttribute('aria-valuenow') || 0); thumb.focus(); key(thumb, 'ArrowRight'); await sleep(10); if (Number(thumb.getAttribute('aria-valuenow')) <= v && v < Number(thumb.getAttribute('aria-valuemax'))) problems.push('slider: ArrowRight did not raise the value'); }
      return problems;
    }""", OPEN_FAMILIES)


CHART_READY = """() => Array.from(document.querySelectorAll('[data-slot="chart"]')).every((c) => { const s = c.querySelector('svg.recharts-surface'); return s && s.getBoundingClientRect().width > 0; })"""


def exercise_chart(page, name, manifest):
    """Hover replay against the hover golden, tooltip dismissal, and the interactive controls."""
    from chart_compare import CHARTS, compare_tooltips, compare_wrappers
    problems = []
    try:
        page.wait_for_function(CHART_READY, timeout=5000)
    except Exception:  # noqa: BLE001
        problems.append('chart: not drawn (no svg.recharts-surface with a size)')
        return problems
    entry = manifest.get(name) or {}
    hover = entry.get('hover')
    if hover:
        page.mouse.move(hover['x'], hover['y'])
        page.wait_for_timeout(250)
        golden = (CHARTS / f'{name}.hover.html').read_text(encoding='utf8')
        ours = page.content()
        problems += ['hover: ' + x for x in compare_wrappers(golden, ours, label='chart')[2]]
        problems += ['hover: ' + x for x in compare_tooltips(golden, ours)]
        page.mouse.move(1279, 899)
        page.wait_for_timeout(150)
        still = page.evaluate("""() => Array.from(document.querySelectorAll('.recharts-tooltip-wrapper')).filter((t) => getComputedStyle(t).visibility === 'visible').length""")
        if still:
            problems.append('hover: the tooltip stays visible after the pointer left the chart')
    # interactive controls redraw the chart
    redraw = page.evaluate(r"""async () => {
      const problems = [];
      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
      const snap = (id) => { const c = document.querySelector(`[data-slot="chart"][data-chart="${id}"] svg.recharts-surface`); return c ? c.innerHTML : ''; };
      const controls = Array.from(document.querySelectorAll('[data-chart-control]'));
      for (const b of controls.filter((c) => c.hasAttribute('data-chart-value'))) {
        if (b.getAttribute('data-active') === 'true') continue;
        const id = b.getAttribute('data-chart-control');
        const before = snap(id);
        b.click(); await sleep(80);
        if (b.getAttribute('data-active') !== 'true') problems.push(`button ${b.getAttribute('data-chart-value')}: data-active not set`);
        if (snap(id) === before) problems.push(`button ${b.getAttribute('data-chart-value')}: chart not redrawn`);
      }
      for (const t of controls.filter((c) => c.getAttribute('data-slot') === 'select-trigger')) {
        const id = t.getAttribute('data-chart-control');
        const content = document.getElementById(t.getAttribute('aria-controls'));
        if (!content) { problems.push('select: no content paired with the trigger'); continue; }
        const items = Array.from(content.querySelectorAll('[data-slot="select-item"]'));
        const next = items.find((i) => i.getAttribute('data-state') !== 'checked');
        if (!next) { problems.push('select: no other item'); continue; }
        const before = snap(id);
        t.click(); await sleep(80);
        next.click(); await sleep(120);
        if (snap(id) === before) problems.push(`select ${next.getAttribute('data-value') || next.textContent.trim()}: chart not redrawn`);
      }
      return problems;
    }""")
    return problems + redraw


SURFACE_JS = """() => { const s = document.querySelector('[data-slot=chart] svg.recharts-surface'); if (!s) return null;
  s.scrollIntoView({ block: 'center' }); const r = s.getBoundingClientRect(); return { left: r.left, top: r.top }; }"""
TOGGLE_STATES_JS = """() => Array.from(document.querySelectorAll('[data-slot="card"] [data-slot="toggle-group-item"]')).map((b) => b.textContent.trim() + '=' + b.getAttribute('data-state'))"""


def _toggle_states(doc_text):
    from lxml import html as lxml_html
    doc = lxml_html.fromstring(doc_text)
    return [re.sub(r'\s+', ' ', b.text_content()).strip() + '=' + (b.get('data-state') or '')
            for b in doc.iter() if isinstance(b.tag, str) and b.get('data-slot') == 'toggle-group-item']


def exercise_block_chart(page, url, entry):
    """A chart inside a block (browser golden out/blocks/<name>.chart*.html, manifest entry blocks/<name>): drawn at the
    block viewport, the drawn wrapper matches the golden; the pointer at the recorded point (relative to the chart
    surface) opens the same tooltip, which hides when the pointer leaves; each range of the ToggleGroup, and a range
    chosen in the Select, redraws the chart to match the golden of that range (the upstream state change), with the
    toggle items in the same state; going back to the initial range matches the base golden again."""
    from chart_compare import GOLDEN as G, compare_tooltips, compare_wrappers
    read = lambda rel: (G / rel).read_text(encoding='utf8')  # noqa: E731
    problems = []
    vp = entry['viewport']

    def drawn():
        try:
            page.wait_for_function(CHART_READY, timeout=5000)
            return True
        except Exception:  # noqa: BLE001
            return False

    def against(rel, label, toggles=True):
        golden = read(rel)
        ours = page.content()
        out = [f'{label}: {x}' for x in compare_wrappers(golden, ours, label='chart')[2]]
        if toggles:
            g, o = _toggle_states(golden), page.evaluate(TOGGLE_STATES_JS)
            if g != o:
                out.append(f'{label}: toggle items golden={g} ours={o}')
        return out

    page.set_viewport_size(vp)
    try:
        page.goto(url, wait_until='load')
        if not drawn():
            return ['block chart: not drawn (no svg.recharts-surface with a size)']
        page.wait_for_timeout(150)
        problems += against(entry['golden'], 'block chart')
        hover = entry.get('hover')
        if hover:
            sr = page.evaluate(SURFACE_JS)
            page.mouse.move(sr['left'] + hover['dx'], sr['top'] + hover['dy'])
            page.wait_for_timeout(250)
            golden = read(hover['golden'])
            ours = page.content()
            problems += ['hover: ' + x for x in compare_wrappers(golden, ours, label='chart')[2]]
            problems += ['hover: ' + x for x in compare_tooltips(golden, ours)]
            page.mouse.move(5, 5)
            page.wait_for_timeout(150)
            still = page.evaluate("""() => Array.from(document.querySelectorAll('.recharts-tooltip-wrapper')).filter((t) => getComputedStyle(t).visibility === 'visible').length""")
            if still:
                problems.append('hover: the tooltip stays visible after the pointer left the chart')
        # ranges: a fresh page, then the real pointer on the toggle group items
        page.goto(url, wait_until='load')
        if not drawn():
            return problems + ['block chart: not drawn on reload']
        for value, v in (entry.get('variants') or {}).items():
            item = page.locator('[data-slot="card"] [data-slot="toggle-group-item"]', has_text=v['label'])
            if item.count() != 1:
                problems.append(f'range {value}: no toggle group item "{v["label"]}"')
                continue
            item.click()
            page.mouse.move(5, 5)
            page.wait_for_timeout(250)
            problems += against(v['golden'], f'range {value} (toggle group)')
        # the Select drives the same state (hidden at this card width, chosen programmatically like a click)
        first = next(iter((entry.get('variants') or {}).items()), None)
        if first:
            value, v = first
            picked = page.evaluate("""(value) => {
              const t = document.querySelector('[data-slot="card"] [data-slot="select-trigger"][data-chart-control]');
              if (!t) return 'no select trigger wired to the chart';
              t.click();
              const content = document.getElementById(t.getAttribute('aria-controls'));
              const item = content && Array.from(content.querySelectorAll('[data-slot="select-item"]')).find((i) => (i.getAttribute('data-value') || i.getAttribute('value')) === value);
              if (!item) return 'no select item ' + value;
              item.click();
              return '';
            }""", value)
            if picked:
                problems.append(f'range {value} (select): {picked}')
            else:
                page.wait_for_timeout(250)
                problems += against(v['golden'], f'range {value} (select)')
        initial = page.locator('[data-slot="card"] [data-slot="toggle-group-item"][data-value="%s"]' % entry.get('initial'))
        if initial.count() == 1:
            initial.click()
            page.mouse.move(5, 5)
            page.wait_for_timeout(250)
            problems += against(entry['golden'], f'range {entry.get("initial")} again')
        else:
            problems.append(f'range {entry.get("initial")}: no toggle group item with data-value')
    finally:
        page.set_viewport_size({'width': 1280, 'height': 900})
    return problems


def main(argv):
    out_json = None
    if '--json' in argv:
        i = argv.index('--json'); out_json = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    from playwright.sync_api import sync_playwright
    from flask_basecoat.testing import make_app
    srv = make_server('127.0.0.1', 0, make_app(), threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_port}'
    comps = sorted(p.stem for p in GOLDEN.glob('*.html'))
    from chart_compare import CHARTS, block_chart, block_names, chart_names
    blocks = block_names()
    targets = [('components', c) for c in comps] + [('blocks', b) for b in blocks] + [('charts', c) for c in chart_names()]
    if argv:
        targets = [t for t in targets if t[1] in argv]
    manifest = json.loads((CHARTS / 'manifest.json').read_text(encoding='utf8'))
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        page.on('console', lambda m: errors.append(f'console.{m.type}: {m.text}') if m.type == 'error' and 'favicon' not in m.text else None)
        for kind, name in targets:
            errors.clear()
            page.goto(f'{base}/basecoat/{kind}/{name}', wait_until='load')
            page.wait_for_timeout(100)
            problems = []
            if kind == 'charts' or name == 'chart':
                try:
                    problems += exercise_chart(page, name, manifest)
                except Exception as e:  # noqa: BLE001
                    problems.append(f'chart exercise failed: {str(e).splitlines()[0]}')
            try:
                problems += exercise(page)
            except Exception as e:  # noqa: BLE001
                problems.append(f'exercise failed: {str(e).splitlines()[0]}')
            bchart = block_chart(name) if kind == 'blocks' else None
            if bchart:
                try:
                    problems += exercise_block_chart(page, f'{base}/basecoat/{kind}/{name}', bchart)
                except Exception as e:  # noqa: BLE001
                    problems.append(f'block chart exercise failed: {str(e).splitlines()[0]}')
            problems = list(errors) + problems
            results.append({'name': name, 'kind': kind, 'status': 'pass' if not problems else 'fail', 'problems': problems})
            print(f"{'PASS' if not problems else 'FAIL'} {kind}/{name}")
            for pr in problems[:8]:
                print('      ', pr[:200])
        browser.close()
    srv.shutdown()
    failed = sum(r['status'] != 'pass' for r in results)
    print(f'\n{len(results) - failed}/{len(results)} pass')
    if out_json:
        pathlib.Path(out_json).write_text(json.dumps(results, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
