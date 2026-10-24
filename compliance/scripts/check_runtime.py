"""Runtime check: every page loads without script errors and its interactive parts behave like Radix.

For each page the browser records page errors and console errors, then exercises what is present:
  dialogs, sheets, drawers, alert dialogs, popovers, dropdown/context menus, menubar menus, selects, comboboxes:
      open from the trigger (click / right-click / hover), content gets data-state="open", Escape closes it and
      focus returns to the trigger (menus, dialogs)
  tabs: ArrowRight moves the active tab; checkbox/switch/toggle: click flips aria-checked / aria-pressed;
  radio groups: click selects; accordion/collapsible: click expands and collapses; sliders: ArrowRight raises the value.
Usage: python compliance/scripts/check_runtime.py [name ...] [--json out.json]
"""
import json
import pathlib
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
      const openOf = (w, kind) => w.querySelector(`[data-slot="${kind === 'menubar-menu' ? 'menubar' : kind}-content"]`) || (kind === 'combobox' && w.querySelector('[data-slot="combobox-content"]'));
      for (const [kind, how] of Object.entries(families)) {
        const wrappers = Array.from(document.querySelectorAll(`[data-fb="${kind}"]`)).slice(0, 4);
        for (const w of wrappers) {
          const trigger = w.querySelector(`[data-slot="${kind === 'menubar-menu' ? 'menubar' : kind}-trigger"], [data-slot="input-group-button"][role=combobox], [data-slot="combobox-input"], [data-slot="combobox-chip-input"]`);
          const content = openOf(w, kind);
          if (!trigger || !content) { problems.push(`${kind}: wrapper without trigger/content`); continue; }
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
          else { esc(); await sleep(60); }
          if (content.getAttribute('data-state') !== 'closed') problems.push(`${kind}: did not close`);
          if (how === 'click' && kind !== 'select' && kind !== 'combobox' && document.activeElement !== trigger && !['tooltip', 'hover-card', 'context-menu'].includes(kind)) problems.push(`${kind}: focus not returned to trigger`);
          await sleep(260);
        }
      }
      // tabs
      for (const tabs of Array.from(document.querySelectorAll('[data-slot="tabs"]')).slice(0, 3)) {
        const triggers = Array.from(tabs.querySelectorAll('[data-slot="tabs-trigger"]'));
        if (triggers.length < 2) continue;
        triggers[0].focus(); key(triggers[0], 'ArrowRight'); await sleep(20);
        if (triggers[1].getAttribute('aria-selected') !== 'true' && triggers[1].getAttribute('data-state') !== 'active') problems.push('tabs: ArrowRight did not activate the next tab');
        triggers[0].click(); await sleep(20);
        if (triggers[0].getAttribute('data-state') !== 'active') problems.push('tabs: click did not activate');
      }
      for (const sel of ['[data-slot="checkbox"]', '[data-slot="switch"]']) {
        const el = Array.from(document.querySelectorAll(sel)).find((e) => !e.disabled);
        if (!el) continue;
        const before = el.getAttribute('aria-checked'); el.click(); await sleep(10);
        if (el.getAttribute('aria-checked') === before) problems.push(`${sel}: click did not toggle aria-checked`);
        el.click();
      }
      const toggle = Array.from(document.querySelectorAll('[data-slot="toggle"]')).find((e) => !e.disabled && !e.closest('[data-slot="toggle-group"]'));
      if (toggle) { const b = toggle.getAttribute('aria-pressed'); toggle.click(); await sleep(10); if (toggle.getAttribute('aria-pressed') === b) problems.push('toggle: click did not toggle aria-pressed'); toggle.click(); }
      const radio = document.querySelector('[data-slot="radio-group"]');
      if (radio) { const items = Array.from(radio.querySelectorAll('[data-slot="radio-group-item"]:not([disabled])')); if (items.length > 1) { items[1].click(); await sleep(10); if (items[1].getAttribute('aria-checked') !== 'true') problems.push('radio-group: click did not select'); } }
      const acc = document.querySelector('[data-slot="accordion-trigger"]');
      if (acc) { const before = acc.getAttribute('aria-expanded'); acc.click(); await sleep(10); if (acc.getAttribute('aria-expanded') === before) problems.push('accordion: click did not toggle'); acc.click(); await sleep(260); }
      const col = document.querySelector('[data-slot="collapsible-trigger"]');
      if (col) { const before = col.getAttribute('aria-expanded'); col.click(); await sleep(10); if (col.getAttribute('aria-expanded') === before) problems.push('collapsible: click did not toggle'); col.click(); await sleep(260); }
      const thumb = Array.from(document.querySelectorAll('[data-slot="slider-thumb"]')).find((t) => !t.closest('[data-slot="slider"][aria-disabled="true"]'));
      if (thumb) { const v = Number(thumb.getAttribute('aria-valuenow') || 0); thumb.focus(); key(thumb, 'ArrowRight'); await sleep(10); if (Number(thumb.getAttribute('aria-valuenow')) <= v && v < Number(thumb.getAttribute('aria-valuemax'))) problems.push('slider: ArrowRight did not raise the value'); }
      return problems;
    }""", OPEN_FAMILIES)


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
    blocks = sorted(p.stem for p in (GOLDEN / 'blocks').glob('*.html'))
    targets = [('components', c) for c in comps] + [('blocks', b) for b in blocks]
    if argv:
        targets = [t for t in targets if t[1] in argv]
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
            try:
                problems = exercise(page)
            except Exception as e:  # noqa: BLE001
                problems = [f'exercise failed: {str(e).splitlines()[0]}']
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
