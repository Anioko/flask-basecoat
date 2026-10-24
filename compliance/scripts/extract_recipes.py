"""Extract the class recipe of every upstream component from the pinned TSX sources.

For each component function in apps/v4/registry/bases/radix/ui/<name>.tsx this records:
  slot            the data-slot the element carries
  element         the JSX tag or Radix primitive it renders
  base_classes    string literals passed to cn()/className unconditionally (order kept, duplicates removed)
  variants        cva variant maps and defaults when the component uses cva
  data_attrs      data-* attributes set from props (data-variant, data-size, data-inset, ...)
The result (compliance/recipes/<name>.json) is the specification each Jinja macro must emit and the
input of the recipe check. It is generated, never edited by hand.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
UI = ROOT / 'upstream/shadcn/radix/ui'
EXTRA = {
    'form': ROOT / 'upstream/shadcn/new-york-v4/ui/form.tsx',
    'toast': ROOT / 'upstream/shadcn/base/ui/toast.tsx',
}
OUT = ROOT / 'recipes'
OUT.mkdir(exist_ok=True)

STR = r'"((?:[^"\\]|\\.)*)"'

# Conditional class strings the regex extractor cannot attribute (ternaries on props). Values are copied
# verbatim from the pinned TSX; `silent_groups` lists pseudo variant groups that emit no data-* attribute.
PATCHES = {
    # Root parts that render no element upstream still need a wrapper macro to group trigger and content.
    'combobox': {'combobox': {'component': 'Combobox', 'element': 'ComboboxPrimitive.Root', 'base_classes': '', 'data_attrs': []}},
    'form': {'form': {'component': 'Form', 'element': 'FormProvider', 'base_classes': '', 'data_attrs': []},
             'form-field': {'component': 'FormField', 'element': 'Controller', 'base_classes': '', 'data_attrs': []}},
    # Indicator spans rendered without a data-slot upstream (menubar and context menu checkbox/radio items).
    'menubar': {
        'menubar-checkbox-item-indicator': {'component': 'MenubarCheckboxItem', 'element': 'span', 'base_classes': 'cn-menubar-checkbox-item-indicator pointer-events-none absolute flex items-center justify-center', 'data_attrs': [], 'no_slot': True},
        'menubar-radio-item-indicator': {'component': 'MenubarRadioItem', 'element': 'span', 'base_classes': 'cn-menubar-radio-item-indicator pointer-events-none absolute flex items-center justify-center', 'data_attrs': [], 'no_slot': True},
    },
    'context-menu': {
        'context-menu-checkbox-item-indicator': {'component': 'ContextMenuCheckboxItem', 'element': 'span', 'base_classes': 'cn-context-menu-item-indicator pointer-events-none', 'data_attrs': [], 'no_slot': True},
        'context-menu-radio-item-indicator': {'component': 'ContextMenuRadioItem', 'element': 'span', 'base_classes': 'cn-context-menu-item-indicator pointer-events-none', 'data_attrs': [], 'no_slot': True},
    },
    'select': {
        'select-item-indicator': {'component': 'SelectItem', 'element': 'span', 'base_classes': 'cn-select-item-indicator', 'data_attrs': [], 'no_slot': True},
        'select-item-text': {'component': 'SelectItem', 'element': 'span', 'base_classes': '', 'data_attrs': [], 'no_slot': True},
        'select-viewport': {'component': 'SelectContent', 'element': 'SelectPrimitive.Viewport', 'base_classes': 'cn-select-viewport data-[position=popper]:h-(--radix-select-trigger-height) data-[position=popper]:w-full data-[position=popper]:min-w-(--radix-select-trigger-width)', 'data_attrs': ['data-position'], 'no_slot': True},
        'select-content': {'variants': {'base': '', 'variants': {'position': {
            'item-aligned': '',
            'popper': 'data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1',
        }}, 'defaults': {'position': 'item-aligned'}}, 'silent_groups': ['position']},
    },
    'tooltip': {'tooltip-arrow': {'component': 'TooltipContent', 'element': 'svg', 'base_classes': 'cn-tooltip-arrow z-50 translate-y-[calc(-50%_-_2px)] bg-foreground fill-foreground', 'data_attrs': [], 'no_slot': True}},
    'drawer': {'drawer-handle': {'component': 'DrawerContent', 'element': 'div', 'base_classes': 'cn-drawer-handle', 'data_attrs': [], 'no_slot': True}},
    'field': {'checkbox-group': {'component': 'FieldGroup', 'element': 'div', 'base_classes': 'cn-field-group group/field-group @container/field-group flex w-full flex-col data-[slot=checkbox-group]:gap-3 [&>[data-slot=field-group]]:gap-4', 'data_attrs': []}},
    'sidebar': {
        'sidebar': {
            'base_classes': '',
            'variants': {'base': '', 'variants': {'collapsible': {
                'none': 'flex h-full w-(--sidebar-width) flex-col bg-sidebar text-sidebar-foreground',
                'offcanvas': 'group peer hidden text-sidebar-foreground md:block',
                'icon': 'group peer hidden text-sidebar-foreground md:block',
            }}, 'defaults': {'collapsible': 'offcanvas'}},
            'silent_groups': ['collapsible'],
        },
        'sidebar-gap': {
            'base_classes': 'cn-sidebar-gap relative w-(--sidebar-width) bg-transparent group-data-[collapsible=offcanvas]:w-0 group-data-[side=right]:rotate-180',
            'variants': {'base': '', 'variants': {'variant': {
                'sidebar': 'group-data-[collapsible=icon]:w-(--sidebar-width-icon)',
                'floating': 'group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4)))]',
                'inset': 'group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4)))]',
            }}, 'defaults': {'variant': 'sidebar'}},
            'silent_groups': ['variant'],
        },
        'sidebar-container': {
            'base_classes': 'fixed inset-y-0 z-10 hidden h-svh w-(--sidebar-width) transition-[left,right,width] duration-200 ease-linear data-[side=left]:left-0 data-[side=left]:group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)] data-[side=right]:right-0 data-[side=right]:group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)] md:flex',
            'variants': {'base': '', 'variants': {'variant': {
                'sidebar': 'group-data-[collapsible=icon]:w-(--sidebar-width-icon) group-data-[side=left]:border-r group-data-[side=right]:border-l',
                'floating': 'p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4))+2px)]',
                'inset': 'p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4))+2px)]',
            }}, 'defaults': {'variant': 'sidebar'}},
            'silent_groups': ['variant'],
        },
    },
}


def balanced(text, start, open_ch, close_ch):
    """Return the index just past the bracket that closes the one at ``start``."""
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def split_functions(src):
    """Yield (name, body) for each top-level component definition."""
    pat = re.compile(r'^(?:export\s+)?(?:function\s+([A-Z]\w*)\s*\(|const\s+([A-Z]\w*)\s*=\s*)', re.M)
    hits = list(pat.finditer(src))
    for i, h in enumerate(hits):
        name = h.group(1) or h.group(2)
        end = hits[i + 1].start() if i + 1 < len(hits) else len(src)
        yield name, src[h.start():end]


def parse_cva(src):
    """Return {varname: {base, variants: {group: {key: classes}}, defaults: {}}} for every cva() call."""
    out = {}
    for m in re.finditer(r'const\s+(\w+)\s*=\s*cva\(\s*' + STR, src):
        name, base = m.group(1), m.group(2)
        call_start = src.index('cva(', m.start())
        call_end = balanced(src, call_start + 3, '(', ')')
        body = src[m.end():call_end]
        variants = {}
        vm = re.search(r'variants:\s*\{', body)
        if vm:
            vend = balanced(body, vm.end() - 1, '{', '}')
            vbody = body[vm.end():vend - 1]
            for gm in re.finditer(r'(\w+|"[^"]+"):\s*\{', vbody):
                group = gm.group(1).strip('"')
                gend = balanced(vbody, gm.end() - 1, '{', '}')
                gbody = vbody[gm.end():gend - 1]
                opts = {}
                for om in re.finditer(r'(\w+|"[^"]+"):\s*' + STR, gbody):
                    opts[om.group(1).strip('"')] = om.group(2).strip()
                if opts:
                    variants[group] = opts
        defaults = {}
        dm = re.search(r'defaultVariants:\s*\{([^}]*)\}', body)
        if dm:
            for om in re.finditer(r'(\w+|"[^"]+"):\s*"?([\w-]+)"?', dm.group(1)):
                defaults[om.group(1).strip('"')] = om.group(2)
        out[name] = {'base': base.strip(), 'variants': variants, 'defaults': defaults}
    return out


def unconditional_strings(arg_src):
    """String literals inside cn(...) that are not guarded by &&, ?: or comparisons."""
    found = []
    depth = 0
    i = 0
    while i < len(arg_src):
        c = arg_src[i]
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
        elif c == '"' and depth == 0:
            j = i + 1
            while j < len(arg_src) and arg_src[j] != '"':
                j += 2 if arg_src[j] == '\\' else 1
            lit = arg_src[i + 1:j]
            before = arg_src[:i].rstrip()
            guarded = before.endswith(('&&', '?', ':', '==', '!=='))
            if not guarded:
                found.append(lit.strip())
            i = j
        i += 1
    return found


JSX_OPEN = re.compile(r'<([A-Za-z][\w.]*)\b')


def jsx_tags(body):
    """Yield (tag, attribute_source) for each JSX opening tag, honouring strings and braces."""
    for m in JSX_OPEN.finditer(body):
        i = m.end()
        depth = 0
        quote = None
        while i < len(body):
            c = body[i]
            if quote:
                if c == '\\':
                    i += 2
                    continue
                if c == quote:
                    quote = None
            elif c in '"\'`':
                quote = c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            elif c == '>' and depth == 0:
                break
            i += 1
        yield m.group(1), body[m.end():i]


def extract(name, path):
    src = path.read_text(encoding='utf8')
    cvas = parse_cva(src)
    comps = {}
    for fname, body in split_functions(src):
        tags = list(jsx_tags(body))
        has_slot = any(re.search(r'data-slot="', attrs) for _, attrs in tags)
        for tag, attrs in tags:
            slot_m = re.search(r'data-slot="([^"]+)"', attrs)
            cls_m = re.search(r'className=\{cn\(|className="([^"]*)"', attrs)
            if not slot_m and not cls_m:
                continue
            classes, used_cva = [], None
            if cls_m:
                if cls_m.group(1) is not None:
                    classes = [cls_m.group(1).strip()]
                else:
                    cn_start = attrs.index('cn(', cls_m.start())
                    cn_end = balanced(attrs, cn_start + 2, '(', ')')
                    inner = attrs[cn_start + 3:cn_end - 1]
                    classes = unconditional_strings(inner)
                    cm = re.search(r'(\w+Variants)\(', inner)
                    if cm and cm.group(1) in cvas:
                        used_cva = cm.group(1)
            data_attrs = sorted(set(re.findall(r'(data-[\w-]+)=\{', attrs)))
            if slot_m:
                key = slot_m.group(1)
            else:
                # slot-less wrappers around another part (InputGroupButton renders <Button>): key by component name
                kebab = re.sub(r'(?<=[a-z0-9])([A-Z])', r'-\1', fname).lower()
                key = kebab if kebab.startswith(name + '-') and tag[0].isupper() and not has_slot else f'{fname}:{tag}'
            entry = {
                'component': fname,
                'element': tag,
                'base_classes': ' '.join(dict.fromkeys(' '.join(classes).split())),
                'data_attrs': data_attrs,
            }
            if used_cva:
                entry['cva'] = used_cva
                entry['variants'] = cvas[used_cva]
            if key in comps:
                # another component renders the same slot (e.g. FieldTitle renders data-slot="field-label" as a div)
                if entry['element'] != comps[key]['element'] and entry['base_classes']:
                    comps[key].setdefault('alts', []).append(entry)
            else:
                comps[key] = entry
    for key, patch in PATCHES.get(name, {}).items():
        comps.setdefault(key, {'component': key, 'element': 'div', 'base_classes': '', 'data_attrs': []}).update(patch)
    if name == 'direction' and not comps:
        # DirectionProvider renders no element; the port exposes a wrapper that sets `dir`.
        comps['direction'] = {'component': 'DirectionProvider', 'element': 'div', 'base_classes': '', 'data_attrs': []}
    return {'name': name, 'source': str(path.relative_to(ROOT)).replace('\\', '/'), 'slots': comps}


def main():
    names = sorted(p.stem for p in UI.glob('*.tsx') if not p.stem.startswith('_'))
    for n in EXTRA:
        if n not in names:
            names.append(n)
    summary = {}
    for n in sorted(names):
        path = EXTRA.get(n, UI / f'{n}.tsx')
        rec = extract(n, path)
        (OUT / f'{n}.json').write_text(json.dumps(rec, indent=2))
        summary[n] = len(rec['slots'])
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
