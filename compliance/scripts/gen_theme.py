"""Generate theme CSS from the pinned upstream sources.

Outputs (both derived, never hand-edited):
  compliance/golden/generated/tokens.css  -> :root / .dark variables from neutral.json
  compliance/golden/generated/theme.css   -> the @theme inline mapping and dark variant from upstream globals.css
The same two files are consumed by the package build so the oracle and the product share one token source.
"""
import json, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
neutral = json.load(open(ROOT / 'upstream/shadcn/neutral.json'))['cssVars']
globals_css = (ROOT / 'upstream/shadcn/site/globals.css').read_text()

def block(selector, vars_):
    body = '\n'.join(f'  --{k}: {v};' for k, v in vars_.items())
    return f'{selector} {{\n{body}\n}}\n'

tokens = block(':root', neutral['light']) + '\n' + block('.dark', neutral['dark'])
(ROOT / 'golden/generated/tokens.css').write_text(tokens)

m = re.search(r'@theme inline \{.*?\n\}\n', globals_css, re.S)
theme = m.group(0)
# The site-only tokens (surface, code, selection, heading font) are not in the registry theme;
# keep the mapping lines but they resolve to nothing unless a consumer defines them.
dark = '@custom-variant dark (&:is(.dark *));\n'
(ROOT / 'golden/generated/theme.css').write_text(dark + '\n' + theme)
print('tokens.css', len(tokens), 'bytes; theme.css', len(theme), 'bytes')
