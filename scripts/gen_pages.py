"""Port the golden upstream pages to Jinja pages built from the component macros.

Input:  compliance/golden/out/<name>.html (React-rendered upstream example) and out/blocks/<name>.html
Output: flask_basecoat/templates/basecoat/pages/components/<name>.html and pages/blocks/<name>.html

Every element carrying data-slot becomes a macro call. Its attributes are translated back into the
macro's semantic keyword arguments (variant, size, open, checked, active, disabled, invalid, orientation,
side, align, href, id ...). Attributes the macro emits on its own are dropped; anything that cannot be
expressed semantically is reported so the macro contract can be extended rather than bypassed.
Lucide SVGs become ``lucide()`` calls. Everything else is copied as plain HTML.

Usage: python scripts/gen_pages.py [name ...] [--force]
"""
import html
import json
import pathlib
import re
import sys

from lxml import etree, html as lxml_html

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flask_basecoat import slots as S  # noqa: E402
from flask_basecoat import icons as I  # noqa: E402

GOLDEN = ROOT / 'compliance' / 'golden' / 'out'
PAGES = ROOT / 'flask_basecoat' / 'templates' / 'basecoat' / 'pages'
FORCE = '--force' in sys.argv

# attributes React/Radix add that carry no meaning for a static port
DROP_ATTRS = {'data-radix-collection-item', 'data-chart', 'data-testid'}
ID_LIKE = {'id', 'aria-controls', 'aria-labelledby', 'aria-describedby', 'for', 'aria-owns', 'aria-activedescendant', 'form'}
PASSTHROUGH = {'href', 'aria-label', 'placeholder', 'value', 'name', 'title', 'alt', 'src', 'style', 'target', 'rel', 'lang', 'maxlength',
               'pattern', 'inputmode', 'autocomplete', 'rows', 'colspan', 'min', 'max', 'step', 'width', 'height', 'required', 'readonly',
               'selected', 'label', 'aria-valuenow', 'aria-valuetext', 'aria-keyshortcuts', 'aria-roledescription', 'aria-required',
               'data-day', 'data-selected-single', 'data-range-start', 'data-range-end', 'data-range-middle', 'data-hidden', 'data-mode',
               'data-week-numbers', 'data-multiple-months', 'data-wrap', 'data-numbered', 'data-shortcut', 'data-shortcuts', 'data-type',
               'data-status', 'data-unchecked', 'data-empty', 'data-visible', 'data-current', 'data-total', 'data-first', 'data-last',
               'data-required', 'data-multiple', 'data-pending-scroll', 'data-dragging', 'data-error', 'data-content', 'data-direction',
               'data-spacing', 'data-viewport', 'data-input-otp-placeholder-shown', 'data-align', 'data-side', 'inert', 'hidden',
               'spellcheck', 'autocorrect', 'autocapitalize', 'novalidate', 'data-collapsible', 'data-active', 'data-size', 'data-variant',
               'aria-hidden', 'aria-expanded', 'aria-live', 'aria-current', 'aria-disabled', 'tabindex', 'data-separator', 'dir',
               'data-mobile', 'data-collapsed', 'data-invalid', 'data-disabled', 'data-placeholder', 'data-highlighted', 'data-selected'}

report = {'pages': 0, 'slots': 0, 'unresolved': []}
AS_CANDIDATES = ['button', 'sidebar-menu-button', 'sidebar-menu-sub-button', 'sidebar-menu-action', 'sidebar-group-label', 'item', 'badge',
                 'card', 'input-group-button', 'marker', 'bubble-content', 'toggle', 'avatar', 'label', 'breadcrumb-link', 'navigation-menu-link',
                 'select-trigger', 'kbd', 'attachment', 'input', 'textarea']


def q(s):
    """Jinja string literal."""
    return "'" + str(s).replace('\\', '\\\\').replace("'", "\\'") + "'"


def kw_literal(kw):
    parts = []
    for k, v in kw.items():
        if v is True:
            parts.append(f'{k}=true')
        elif v is False:
            parts.append(f'{k}=false')
        elif v is None:
            parts.append(f'{k}=none')
        elif isinstance(v, dict):
            inner = ', '.join(f'{q(a)}: {q(b) if not isinstance(b, bool) else str(b).lower()}' for a, b in v.items())
            parts.append(f'{k}={{{inner}}}')
        else:
            parts.append(f'{k}={q(v)}')
    return ', '.join(parts)


def classes_of(el):
    return (el.get('class') or '').split()


def translate(el, slot_name):
    """Return (kwargs, extra_class) so that slot(slot_name, kwargs, extra_class) reproduces el's attributes."""
    attrs = dict(el.attrib)
    attrs.pop('data-slot', None)
    attrs.pop('class', None)
    for d in DROP_ATTRS:
        attrs.pop(d, None)
    kw = {}
    have = classes_of(el)
    have_set = set(have)
    # composite parts (a Button carrying another part's cva) are recognised by their marker class
    for cname, comp in S.COMPOSITES.items():
        if slot_name == comp['outer'] and comp['marker'] in have_set:
            slot_name = cname
        elif slot_name == cname:
            kw['data_slot'] = cname
    rec = S.recipe(slot_name, el.tag if el.tag != S.tag_for(slot_name, attrs.get('href')) else None)
    # asChild detection: which part's recipe do the classes carry?
    if slot_name in S.AS_BUTTON or slot_name.endswith('-trigger') or slot_name in ('item', 'field-label'):
        best = None
        for cand in AS_CANDIDATES:
            crec = S.recipe(cand)
            cbase = set(crec.get('base_classes', '').split()) | set(((crec.get('variants') or {}).get('base', '')).split())
            cbase.discard('')
            if cbase and cbase <= have_set:
                if best is None or len(cbase) > best[1]:
                    best = (cand, len(cbase))
        default_as = 'button' if slot_name in S.AS_BUTTON else None
        chosen_as = best[0] if best else None
        if chosen_as != default_as:
            kw['as_'] = chosen_as
    # tag override when upstream rendered a different element (asChild with a plain element)
    default_tag = S.tag_for(slot_name, attrs.get('href'))
    if el.tag != default_tag and el.tag != 'svg':
        kw['tag'] = el.tag
    groups = set(((rec.get('variants') or {}).get('variants') or {}).keys())
    as_name = S.as_slot_for(slot_name, kw)
    if as_name:
        groups |= set(((S.recipe(as_name).get('variants') or {}).get('variants') or {}).keys())
    for g in list(groups) + ['variant', 'size', 'spacing']:
        if f'data-{g}' in attrs and not (slot_name == 'sidebar' and g == 'collapsible'):
            kw[g] = attrs.pop(f'data-{g}')
    # cva groups without a data-* mirror (toggle, alert, sidebar conditionals): infer the option from the classes.
    # tailwind-merge may have removed some option classes, so the best-covered option wins.
    for source in (rec, S.recipe(as_name) if as_name else {}):
        for g, options in ((source.get('variants') or {}).get('variants') or {}).items():
            if g in kw:
                continue
            default = (source.get('variants') or {}).get('defaults', {}).get(g)
            scored = []
            for opt, cls in options.items():
                toks = set(cls.split())
                if toks:
                    scored.append((len(toks & have_set) / len(toks), opt))
            scored.sort(reverse=True)
            if scored and scored[0][0] >= 0.5:
                best = scored[0][1]
                if best == default or (len(scored) > 1 and scored[1][0] == scored[0][0] and default in (scored[0][1], scored[1][1])):
                    continue
                kw[g] = best
            else:
                kw[g] = None
    # svg parts: the icon is named by its lucide class
    if el.tag == 'svg':
        icon = next((c[len('lucide-'):] for c in have if c.startswith('lucide-')), None)
        if icon and icon != S.SVG_ICON.get(slot_name):
            kw['icon'] = icon
        for k in list(S.SVG_CONST):
            attrs.pop(k.lower(), None); attrs.pop(k, None)
        have = [c for c in have if c not in ('lucide', f'lucide-{icon}')]
        have_set = set(have)
    # expected classes from recipe + variants; the remainder is the caller's class
    want, _ = S.classes_for(slot_name, {k: v for k, v in kw.items() if isinstance(v, str) or v is None})
    extra = [c for c in have if c not in set(want)]
    merged = set(S.classes_for(slot_name, {k: v for k, v in kw.items() if isinstance(v, str) or v is None}, ' '.join(extra))[0])
    if merged != have_set:
        report['unresolved'].append(f'{slot_name}: class merge mismatch: ours-only={sorted(merged - have_set)[:5]} golden-only={sorted(have_set - merged)[:5]}')

    # state attributes
    ds = attrs.pop('data-state', None)
    if slot_name in S.OPEN_SLOTS and ds in ('open', 'closed'):
        if ds == 'open':
            kw['open'] = True
        elif slot_name in S.OPTIONAL_OPEN:
            kw['open'] = False
        attrs.pop('aria-expanded', None)
        attrs.pop('hidden', None)
    elif slot_name in S.OPTIONAL_OPEN and ds is None:
        pass
    elif slot_name in S.CHECKED_SLOTS and ds in ('checked', 'unchecked', 'indeterminate'):
        kw['checked'] = ds == 'checked' if ds != 'indeterminate' else 'indeterminate'
        attrs.pop('aria-checked', None)
        if slot_name in ('checkbox', 'switch', 'radio-group-item'):
            v = attrs.pop('value', 'on')
            if v != 'on':
                kw['value'] = v
    elif slot_name in S.PRESSED_SLOTS and ds in ('on', 'off'):
        if ds == 'on':
            kw['pressed'] = True
        if attrs.get('role') == 'radio':
            attrs.pop('role', None); attrs.pop('aria-checked', None)
        else:
            attrs.pop('aria-pressed', None)
            kw['multiple'] = True
    elif slot_name in S.ACTIVE_SLOTS and ds in ('active', 'inactive'):
        if ds == 'active':
            kw['active'] = True
        attrs.pop('aria-selected', None); attrs.pop('hidden', None)
    elif slot_name in ('progress', 'progress-indicator'):
        attrs.pop('data-max', None); attrs.pop('aria-valuemax', None); attrs.pop('aria-valuemin', None)
        if ds != 'indeterminate':
            report['unresolved'].append(f'{slot_name}: data-state={ds}')
    elif slot_name == 'sidebar' and ds in ('expanded', 'collapsed'):
        if ds == 'collapsed':
            kw['collapsed'] = True
    elif slot_name == 'table-row' and ds is not None:
        kw['selected'] = ds == 'selected'
    elif ds is not None:
        kw['data_state'] = ds
    if slot_name == 'toggle-group':
        role = attrs.pop('role', None)
        if role == 'toolbar':
            kw['multiple'] = True

    dd = attrs.pop('data-disabled', None)
    if attrs.pop('disabled', None) is not None or (dd is not None and dd != 'false'):
        kw['disabled'] = True
    if attrs.pop('aria-invalid', None) == 'true':
        kw['invalid'] = True
        attrs.pop('data-invalid', None)
    if attrs.pop('data-invalid', None) == 'true':
        kw['invalid'] = True
    if attrs.pop('required', None) is not None:
        kw['required'] = True
    if attrs.pop('readonly', None) is not None:
        kw['readonly'] = True
    if 'data-inset' in attrs:
        attrs.pop('data-inset'); kw['inset'] = True
    if 'data-orientation' in attrs:
        o = attrs.pop('data-orientation')
        attrs.pop('aria-orientation', None)
        kw['orientation'] = o
    if slot_name == 'pagination-link' and attrs.get('aria-current') == 'page':
        attrs.pop('aria-current'); attrs.pop('data-active', None); kw['active'] = True
    if slot_name in ('sidebar-menu-button', 'sidebar-menu-sub-button', 'input-otp-slot', 'message-scroller-button', 'dropdown-menu-trigger', 'collapsible-trigger') and 'data-active' in attrs:
        kw['active'] = attrs.pop('data-active') == 'true'
    if slot_name == 'select-trigger':
        if attrs.pop('data-placeholder', None) is None:
            kw['placeholder_shown'] = False
    if slot_name == 'slider-thumb':
        mn, mx = attrs.pop('aria-valuemin', '0'), attrs.pop('aria-valuemax', '100')
        if 'tabindex' in attrs:
            attrs.pop('tabindex')
        if mn != '0':
            kw['min'] = mn
        if mx != '100':
            kw['max'] = mx
        if 'aria-valuenow' in attrs:
            kw['value'] = attrs.pop('aria-valuenow')
    if slot_name == 'questionnaire-progress':
        kw['current'] = attrs.pop('data-current', '1'); kw['total'] = attrs.pop('data-total', '1')
        for a in ('aria-valuemax', 'aria-valuenow', 'aria-valuetext', 'data-first', 'data-last', 'aria-valuemin'):
            attrs.pop(a, None)

    # constants and defaults the slot emits on its own
    for table in (S.CONST.get(slot_name, {}), S.DEFAULT_ATTRS.get(slot_name, {})):
        for k, v in table.items():
            if attrs.get(k) == v:
                attrs.pop(k)
    if as_name and as_name != 'button':
        for table in (S.CONST.get(as_name, {}), S.DEFAULT_ATTRS.get(as_name, {})):
            for k, v in table.items():
                if attrs.get(k) == v:
                    attrs.pop(k)
    if slot_name in S.ACTIVE_FLAG_SLOTS or as_name in S.ACTIVE_FLAG_SLOTS:
        if 'data-active' in attrs:
            kw['active'] = attrs.pop('data-active') == 'true'
    # type / href / id
    if 'type' in attrs:
        kw['type'] = attrs.pop('type')
    if 'href' in attrs:
        kw['href'] = attrs.pop('href')
    for k in list(attrs):
        if k in ID_LIKE:
            v = attrs.pop(k)
            if k == 'id':
                kw['id'] = v
            elif k == 'for':
                kw['for_'] = v
            else:
                kw[k.replace('-', '_')] = v
    if 'dir' in attrs:
        kw['dir'] = attrs.pop('dir')
    if 'data-side' in attrs:
        kw['side'] = attrs.pop('data-side')
    if 'data-align' in attrs:
        kw['align'] = attrs.pop('data-align')
    if attrs.get('aria-current') == 'page':
        attrs.pop('aria-current'); kw['current'] = True
    # remaining: pass through, but remember ones that are state-like so the contract can grow
    if attrs.get('aria-invalid') == 'false':
        attrs.pop('aria-invalid')
    leftover = {}
    for k, v in attrs.items():
        if k in PASSTHROUGH or k.startswith('data-') or k.startswith('aria-') or k in ('tabindex', 'role', 'hidden', 'inert', 'target', 'rel'):
            leftover[k] = v
        else:
            leftover[k] = v
            report['unresolved'].append(f'{slot_name}: attribute {k}={v!r}')
    return kw, ' '.join(extra), leftover, slot_name


def is_lucide(el):
    cls = classes_of(el)
    return el.tag == 'svg' and 'lucide' in cls and any(c.startswith('lucide-') for c in cls)


def lucide_call(el):
    cls = classes_of(el)
    name = next(c[len('lucide-'):] for c in cls if c.startswith('lucide-'))
    extra = [c for c in cls if c not in ('lucide', f'lucide-{name}')]
    inner = ''.join(etree.tostring(ch, encoding='unicode', method='html') for ch in el)
    inner = re.sub(r'\s+', ' ', inner).replace('> <', '><').strip()
    known = I.ICONS.get(name)
    if known is None or re.sub(r'\s|"', '', known) != re.sub(r'\s|"', '', inner.replace("'", '"')):
        return None
    attrs = {k: v for k, v in el.attrib.items() if k not in ('xmlns', 'width', 'height', 'viewbox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'class')}
    kw = ', '.join(f'{k.replace("-", "_")}={q(v)}' for k, v in attrs.items())
    return f"{{{{ lucide({q(name)}, {q(' '.join(extra))}{', ' + kw if kw else ''}) }}}}"


def text_literal(t):
    if not t:
        return ''
    out = html.escape(t, quote=False)
    return out.replace('{{', '{{ "{{" }}').replace('{%', '{{ "{%" }}').replace('{#', '{{ "{#" }}')


def render_node(el, depth, ctx):
    pad = ''  # React emits no whitespace between elements; the generator emits none either
    out = []
    tag = el.tag if isinstance(el.tag, str) else None
    if tag is None:
        return ''
    slot_name = el.get('data-slot')
    # Preformatted parts (pre/code or whitespace-pre* containers) keep their inner markup verbatim: template
    # indentation would otherwise become visible whitespace.
    preformatted = tag in PRE_TAGS or any(c.startswith('whitespace-pre') for c in classes_of(el))
    if preformatted and slot_name:
        full = etree.tostring(el, encoding='unicode', method='html', with_tail=False).replace('&amp;', '&')
        inner = full[full.index('>') + 1:full.rindex('<')]
        kw, extra, leftover, slot_name = translate(el, slot_name)
        if extra:
            kw['class'] = extra
        if leftover:
            kw['attrs'] = leftover
        if 'tag' not in kw and tag != S.tag_for(slot_name, el.get('href')) and tag != 'svg':
            kw['tag'] = tag
        report['slots'] += 1
        macro = 'ui.' + slot_name.replace('-', '_')
        return f"{{% call {macro}({kw_literal(kw)}) %}}{{% raw %}}{inner}{{% endraw %}}{{% endcall %}}"
    children = ''.join(render_children(el, depth + 1, ctx))
    text_before = text_literal(el.text)
    if slot_name:
        report['slots'] += 1
        # example chrome uses the shared macros
        if slot_name == 'example-wrapper':
            extra = ' '.join(c for c in classes_of(el) if c not in set(EXAMPLE_WRAPPER_CLASSES))
            kw = {'class': extra} if extra else {}
            return f"{{% call ui.example_wrapper({kw_literal(kw)}) %}}\n{children}{{% endcall %}}\n"
        if slot_name == 'example':
            title = None
            content = None
            for ch in el:
                if ch.get('data-slot') == 'example-content':
                    content = ch
                elif isinstance(ch.tag, str):
                    title = (ch.text_content() or '').strip()
            kw = {}
            if title:
                kw['title'] = title
            cextra = ' '.join(c for c in classes_of(content) if c not in set(EXAMPLE_CONTENT_CLASSES)) if content is not None else ''
            eextra = ' '.join(c for c in classes_of(el) if c not in set(EXAMPLE_CLASSES))
            if cextra:
                kw['class'] = cextra
            if eextra:
                kw['container_class'] = eextra
            inner = ''.join(render_children(content, depth + 1, ctx)) if content is not None else ''
            return f"{{% call ui.example({kw_literal(kw)}) %}}{inner}{{% endcall %}}\n"
        if slot_name == 'example-content':
            return children
        kw, extra, leftover, slot_name = translate(el, slot_name)
        if extra:
            kw['class'] = extra
        if leftover:
            kw['attrs'] = leftover
        macro = 'ui.' + slot_name.replace('-', '_')
        if slot_name not in S.RECIPES and slot_name not in S.VIRTUAL:
            report['unresolved'].append(f'no macro for slot {slot_name}')
            macro = None
        if macro is None:
            return raw_element(el, depth, ctx, children, text_before)
        if S.tag_for(slot_name) in S.VOID or (not children.strip() and not text_before.strip()):
            if text_before.strip():
                kw['text'] = el.text
            return f"{{{{ {macro}({kw_literal(kw)}) }}}}"
        return f"{{% call {macro}({kw_literal(kw)}) %}}{text_before}{children}{{% endcall %}}"
    if is_lucide(el):
        call = lucide_call(el)
        if call:
            return f"{call}"
    return raw_element(el, depth, ctx, children, text_before)


PRE_TAGS = {'pre', 'code', 'textarea', 'script', 'style'}


def in_pre(el):
    node = el.getparent() if el is not None else None
    while node is not None:
        if isinstance(node.tag, str) and node.tag in PRE_TAGS:
            return True
        node = node.getparent()
    return False


def raw_element(el, depth, ctx, children, text_before):
    pad = ''
    tag = el.tag
    if tag in PRE_TAGS:
        # whitespace is content here: emit the subtree exactly as upstream rendered it
        return etree.tostring(el, encoding='unicode', method='html', with_tail=False).replace('&amp;', '&')
    attrs = []
    for k, v in el.attrib.items():
        if k in DROP_ATTRS:
            continue
        if k == 'class':
            attrs.append(f' class="{v.replace(chr(34), "&quot;")}"')  # Tailwind scans the raw class names ([&>button]:line-through)
        else:
            attrs.append(f' {k}="{html.escape(v, quote=True)}"' if v != '' else f' {k}=""')
    open_tag = f"<{tag}{''.join(attrs)}>"
    if tag in S.VOID:
        return f"{open_tag}"
    if not children.strip():
        return f"{open_tag}{text_before}</{tag}>"
    return f"{open_tag}{text_before}{children}</{tag}>"


def render_children(el, depth, ctx):
    out = []
    if isinstance(el.tag, str) and el.tag in PRE_TAGS:
        return out
    for ch in el:
        if isinstance(ch.tag, str):
            out.append(render_node(ch, depth, ctx))
        tail = text_literal(ch.tail)
        # React keeps explicit spaces ({" "}); whitespace-only tails that contain a newline are JSX formatting
        if tail.strip() or (tail and '\n' not in tail):
            out.append(tail)
    return out


EXAMPLE_WRAPPER_CLASSES = 'mx-auto grid min-h-screen w-full max-w-5xl min-w-0 content-center items-start gap-8 p-4 pt-2 sm:gap-12 sm:p-6 md:grid-cols-2 md:gap-8 lg:p-12 2xl:max-w-6xl'.split()
EXAMPLE_CLASSES = 'mx-auto flex w-full max-w-lg min-w-0 flex-col gap-1 self-stretch lg:max-w-none'.split()
EXAMPLE_CONTENT_CLASSES = "flex min-w-0 flex-1 flex-col items-start gap-6 rounded-xl bg-card p-12 text-foreground style-lyra:rounded-none style-sera:rounded-none *:[div:not([class*='w-'])]:w-full".split()


PROTECT = re.compile(r'({% raw %}.*?{% endraw %}|<pre\b.*?</pre>|<textarea\b.*?</textarea>|<script\b.*?</script>|<style\b.*?</style>|<[a-z]+\b[^>]*whitespace-pre[^>]*>.*?</(?:div|span|p)>|{% call [^%]*whitespace-pre[^%]*%}.*?{% endcall %})', re.S)
BLOCK_TAG = re.compile(r'({%-?\s*(?:endcall|endblock|endfor|endif|set|block|import|extends)\b[^%]*%}|{#[^#]*#})[ \t]*\n[ \t]*')
WS_RUN = re.compile(r'[ \t]*\n[ \t]*')


def compact(text):
    """Remove template indentation between tags and text. React emits no whitespace text nodes between elements,
    so any newline/indent the generator adds would become a visible space in inline formatting contexts."""
    parts = PROTECT.split(text)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
            continue
        part = BLOCK_TAG.sub(lambda m: m.group(1) + '\n', part)
        # every other whitespace run that contains a newline is template indentation
        # remove the newline and the indentation after it; spaces before a newline are content (JSX {" "})
        part = re.sub(r'(?<!%}|#})\n[ \t]*', '', part)
        out.append(part)
    return ''.join(out)


def convert(kind, name):
    src = (GOLDEN / ('blocks' if kind == 'blocks' else '') / f'{name}.html').read_text(encoding='utf8')
    doc = lxml_html.fromstring(src)
    body = doc.find('body')
    ctx = {}
    parts = []
    # The example wrapper is wrapped upstream in <div class="w-full bg-muted dark:bg-background">; the macro provides it.
    for ch in body:
        if isinstance(ch.tag, str) and ch.tag == 'div' and set(classes_of(ch)) == {'w-full', 'bg-muted', 'dark:bg-background'} and len(ch) == 1 and ch[0].get('data-slot') == 'example-wrapper':
            parts.append(render_node(ch[0], 1, ctx))
        elif isinstance(ch.tag, str):
            parts.append(render_node(ch, 1, ctx))
    inner = ''.join(parts)
    title = f'{name} · Flask-Basecoat'
    page = (
        "{% extends 'basecoat/pages/_layout.html' %}\n"
        "{% import 'basecoat/index.html' as ui %}\n"
        f"{{# Port of the upstream shadcn/ui {'block' if kind == 'blocks' else 'example'} `{name}` (pinned source in compliance/upstream). #}}\n"
        f"{{% block title %}}{title}{{% endblock %}}\n"
        "{% block body %}\n" + inner + "{% endblock %}\n"
    )
    out = PAGES / kind / f'{name}.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not FORCE:
        return False
    out.write_text(compact(page), encoding='utf8')
    report['pages'] += 1
    return True


def main(argv):
    names = [a for a in argv if not a.startswith('--')]
    comps = sorted(p.stem for p in GOLDEN.glob('*.html'))
    blocks = sorted(p.stem for p in (GOLDEN / 'blocks').glob('*.html') if '.' not in p.stem)  # <name>.chart*.html are chart goldens
    targets = [('components', c) for c in comps] + [('blocks', b) for b in blocks]
    # dashboard-01's chart is drawn from a spec wired by hand (see scripts/gen_dashboard01_chart_spec.py); regenerating
    # the page from its server-rendered golden would bring back the empty chart, so it is skipped unless named.
    if 'dashboard-01' not in names:
        targets = [t for t in targets if t != ('blocks', 'dashboard-01')]
    if names:
        targets = [t for t in targets if t[1] in names]
    for kind, name in targets:
        try:
            convert(kind, name)
        except Exception as e:  # keep going; report at the end
            report['unresolved'].append(f'{kind}/{name}: {type(e).__name__}: {e}')
    uniq = sorted(set(report['unresolved']))
    print(json.dumps({'pages': report['pages'], 'slots': report['slots'], 'unresolved': len(uniq)}))
    for u in uniq[:80]:
        print('  ', u)


if __name__ == '__main__':
    main(sys.argv[1:])
