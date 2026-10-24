"""Generate flask_basecoat/icons.py from the Lucide static SVG set.

Collects every icon name referenced by the pinned upstream sources (lucide="XxxIcon" props and
lucide-react imports) and embeds the SVG path markup so templates can render identical icons
without a client-side icon script. Run: python scripts/gen_icons.py
"""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
UP = ROOT / 'compliance/upstream/shadcn'
ICONS = ROOT / 'compliance/golden/node_modules/lucide-static/icons'

def kebab(name):
    name = re.sub(r'Icon$', '', name)
    s = re.sub(r'(?<=[a-z0-9])([A-Z])', r'-\1', name)
    s = re.sub(r'(?<=[A-Z])([A-Z][a-z])', r'-\1', s)
    s = re.sub(r'(?<=[a-zA-Z])([0-9])', r'-\1', s)
    return s.lower()

ALIASES = {
    'loader-2': 'loader-circle', 'more-horizontal': 'ellipsis', 'more-vertical': 'ellipsis-vertical',
    'alert-circle': 'circle-alert', 'alert-triangle': 'triangle-alert', 'check-circle': 'circle-check',
    'check-circle-2': 'circle-check', 'x-circle': 'circle-x', 'help-circle': 'circle-help', 'plus-circle': 'circle-plus',
    'minus-circle': 'circle-minus', 'arrow-up-circle': 'circle-arrow-up', 'grip-vertical': 'grip-vertical',
    'bar-chart': 'chart-bar', 'bar-chart-2': 'chart-bar-big', 'bar-chart-3': 'chart-column', 'line-chart': 'chart-line',
    'pie-chart': 'chart-pie', 'sliders-horizontal': 'sliders-horizontal', 'layout-dashboard': 'layout-dashboard',
    'edit': 'pen', 'edit-2': 'pen', 'edit-3': 'pen-line', 'trash-2': 'trash-2', 'octagon-x': 'octagon-x',
    'info': 'info', 'send-horizonal': 'send-horizontal', 'circle-dashed': 'circle-dashed',
}

names = set()
for f in UP.rglob('*.tsx'):
    t = f.read_text(encoding='utf8', errors='ignore')
    names.update(re.findall(r'lucide="([A-Za-z0-9]+)"', t))
    for m in re.finditer(r'import \{([^}]*)\} from "lucide-react"', t):
        names.update(x.strip().split(' as ')[0].strip() for x in m.group(1).split(',') if x.strip())

# Icons the Flask package itself uses in macros (close buttons, chevrons, checks, dots, menus, etc.)
names.update(['XIcon','CheckIcon','ChevronDownIcon','ChevronUpIcon','ChevronRightIcon','ChevronLeftIcon','ChevronsUpDownIcon',
              'CircleIcon','MinusIcon','PlusIcon','SearchIcon','EllipsisIcon','MoreHorizontalIcon','PanelLeftIcon','GripVerticalIcon',
              'Loader2Icon','LoaderCircleIcon','CopyIcon','ArrowDownIcon','ArrowUpIcon','ArrowLeftIcon','ArrowRightIcon','CalendarIcon','InfoIcon',
              'CircleAlertIcon','TriangleAlertIcon','CircleCheckIcon','OctagonXIcon','MenuIcon','SunIcon','MoonIcon','SquareIcon','DotIcon'])
# Icons used by the dashboard example screens.
names.update(['LightbulbIcon','MegaphoneIcon','PackageIcon','UserPlusIcon','UserCheckIcon','HandshakeIcon','CircleDollarSignIcon',
              'LandmarkIcon','ReceiptIcon','RocketIcon','StickyNoteIcon','TicketIcon','NotebookPenIcon','LayersIcon','ChartColumnIcon',
              'ChartNoAxesColumnIcon','ArrowUpDownIcon','MapPinIcon','TruckIcon','StoreIcon','CalendarDaysIcon','CircleCheckBigIcon',
              'BanknoteIcon','PiggyBankIcon','MousePointerClickIcon','PercentIcon','FunnelIcon','ShieldCheckIcon','KeyRoundIcon','LogInIcon',
              'GiftIcon','AwardIcon','BriefcaseIcon','TargetIcon','GlobeIcon','ChartPieIcon','ChartLineIcon','ChartAreaIcon','MonitorIcon',
              'ShoppingBagIcon','UsersIcon','TrophyIcon','ActivityIcon','EllipsisVerticalIcon','SparklesIcon','ArrowUpRightIcon','ArrowDownRightIcon',
              'TrendingUpIcon','TrendingDownIcon','LayoutDashboardIcon','FileTextIcon','MailIcon','PhoneIcon','VideoIcon','MessageSquareIcon',
              'SettingsIcon','HouseIcon','ClipboardListIcon','KanbanIcon','WalletIcon','CreditCardIcon','CirclePlayIcon','FlameIcon','HeartIcon'])
# Icons used by the app example screens (mail, chat, music, social, calendar, boards).
names.update(['ForwardIcon','ReplyIcon','ReplyAllIcon','PuzzleIcon','SkipBackIcon','SkipForwardIcon','ShuffleIcon','LibraryIcon',
              'Repeat2Icon','RepeatIcon','CalendarCheckIcon','MessagesSquareIcon','UsersRoundIcon','ArchiveXIcon','MousePointerClickIcon'])

# Icons used by the marketing example screens.
names.update(['Share2Icon','PlayIcon','PauseIcon','CircleXIcon','CircleCheckIcon','LoaderCircleIcon'])

# Icons used by the content example screens (blog, changelog, updates, roadmap, timeline, activity, projects, playground).
names.update(['PanelTopIcon','BookOpenTextIcon','ClipboardCheckIcon','ImageUpIcon','ListTodoIcon','CookieIcon','PartyPopperIcon',
              'ExternalLinkIcon','ClockIcon','TagIcon','FilterIcon','RotateCcwIcon','SendIcon','MessageCircleIcon','UserIcon'])

# Icons used by the commerce example screens (cart, checkout, products, settings, profile, onboarding).
names.update(['Grid3X3Icon','BoxIcon','UploadIcon','KeyIcon','FactoryIcon'])

# Icons used by the admin example screens (dashboards, file managers, point of sale, tasks, todo list).
names.update(['DiamondIcon','UploadIcon','HeadphonesIcon','ChevronFirstIcon','ChevronLastIcon','HistoryIcon','WarehouseIcon',
              'QrCodeIcon','CircleOffIcon','FolderPlusIcon','FileIcon','EyeIcon','EyeOffIcon','Building2Icon','ImageIcon','ListIcon',
              'FunnelIcon','CircleHelpIcon','ColumnsIcon','Columns3Icon','LoaderIcon','CircleDashedIcon','FileChartColumnIcon',
              'GripVerticalIcon','TimerIcon','Settings2Icon','DownloadIcon','InfoIcon','CalendarDaysIcon','StarIcon','QrCodeIcon'])

out, missing = {}, []
for n in sorted(names):
    k = kebab(n)
    k = ALIASES.get(k, k)
    p = ICONS / f'{k}.svg'
    if not p.exists():
        missing.append((n, k)); continue
    svg = p.read_text(encoding='utf8')
    inner = re.search(r'<svg[^>]*>(.*)</svg>', svg, re.S).group(1).strip()
    inner = re.sub(r'\s+', ' ', inner).replace('> <', '><')
    out[k] = inner

py = ['"""Lucide icon paths used by Flask-Basecoat (generated by scripts/gen_icons.py; do not edit)."""',
      'ICONS = ' + json.dumps(out, indent=0, sort_keys=True), '',
      'def svg(name, class_name="", **attrs):',
      '    """Return the full <svg> markup for a Lucide icon with the attributes lucide-react emits."""',
      '    from markupsafe import Markup, escape',
      '    body = ICONS.get(name)',
      '    if body is None:',
      '        raise KeyError(f"unknown lucide icon: {name}")',
      '    classes = " ".join(c for c in ["lucide", f"lucide-{name}", class_name] if c)',
      '    extra = "".join(f\' {k.replace("_", "-")}="{escape(v)}"\' for k, v in attrs.items() if v is not None)',
      '    return Markup(f\'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{classes}"{extra}>{body}</svg>\')',
      '']
(ROOT / 'flask_basecoat/icons.py').write_text('\n'.join(py), encoding='utf8')
print(len(out), 'icons embedded;', len(missing), 'unresolved:', missing[:40])
