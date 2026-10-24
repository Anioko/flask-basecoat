"""Developer helper: compare one or more chart pages with their goldens and print the differences.

Usage: python compliance/scripts/chart_diff.py chart-area-default [chart-bar-default ...] [--hover] [--save DIR]
--hover replays the pointer position recorded in out/charts/manifest.json and compares with <name>.hover.html.
--save writes our rendered page to DIR/<name>.html for inspection.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from chart_compare import CHARTS, EXTRA, GOLDEN, ChartBrowser, compare_tooltips, compare_wrappers, reduce_wrapper, wrappers_of  # noqa: E402


def main(argv):
    hover = '--hover' in argv
    save = None
    if '--save' in argv:
        save = pathlib.Path(argv[argv.index('--save') + 1])
        argv = [a for a in argv if a != str(save)]
    names = [a for a in argv if not a.startswith('--')]
    manifest = json.loads((CHARTS / 'manifest.json').read_text(encoding='utf8'))
    manifest.update(json.loads((EXTRA / 'manifest.json').read_text(encoding='utf8')) if (EXTRA / 'manifest.json').exists() else {})
    b = ChartBrowser()
    try:
        for name in names:
            path = '/basecoat/components/chart' if name == 'chart' else f'/basecoat/charts/{name}'
            home = EXTRA if (EXTRA / f'{name}.html').exists() else CHARTS
            gfile = GOLDEN / 'chart.html' if name == 'chart' else home / f'{name}.html'
            status, ours = b.load(path)
            if hover:
                h = manifest[name]['hover']
                if h.get('relativeTo') == 'surface':  # our page frames the chart differently from the harness
                    box = b.page.locator('[data-slot=chart] svg.recharts-surface').first.bounding_box()
                    b.page.mouse.move(box['x'] + h['dx'], box['y'] + h['dy'])
                else:
                    b.page.mouse.move(h['x'], h['y'])
                b.page.wait_for_timeout(250)
                ours = b.page.content()
                gfile = home / f'{name}.hover.html'
            gold = gfile.read_text(encoding='utf8')
            if save:
                save.mkdir(parents=True, exist_ok=True)
                (save / f'{name}{".hover" if hover else ""}.html').write_text(ours, encoding='utf8')
            gc, oc, problems = compare_wrappers(gold, ours)
            if hover:
                problems += compare_tooltips(gold, ours)
            gw, ow = wrappers_of(gold), wrappers_of(ours)
            sizes = [(len(reduce_wrapper(g)), len(reduce_wrapper(o))) for g, o in zip(gw, ow)]
            print(f"{'PASS' if not problems else 'FAIL'} {name} wrappers={gc}/{oc} elements={sizes} errors={b.errors[:3]}")
            for p in problems[:40]:
                print('   ', p)
            if len(problems) > 40:
                print(f'    ... {len(problems) - 40} more')
    finally:
        b.close()


if __name__ == '__main__':
    main(sys.argv[1:])
