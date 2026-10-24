"""Capability-map helpers: grouping by capability_type, and the maturity ramp the maps are drawn with.

Entelim stores each capability's type in one field, ``capability_type``, with three values: strategic, operational and
supporting. The capability-map macros take that field from the data they are given and group by it, in that order. A
capability whose type is empty (or not one of the three) goes in a final group, "Type not set", and is never dropped.
Nothing else is read as a type: not ``type``, not ``domain``, not the parent's value.
"""
TYPE_FIELD = 'capability_type'
TYPES = [('strategic', 'Strategic'), ('operational', 'Operational'), ('supporting', 'Supporting')]
UNSET = ('unset', 'Type not set')


def type_of(capability):
    """The capability's own type: one of the three keys, or '' when it has none."""
    value = (capability.get(TYPE_FIELD) or '') if hasattr(capability, 'get') else ''
    value = str(value).strip().lower()
    return value if value in dict(TYPES) else ''


def type_label(capability):
    return dict(TYPES).get(type_of(capability), UNSET[1])


def capability_groups(items, descriptions=None):
    """[{'key', 'label', 'description', 'items'}] in the order strategic, operational, supporting, then "Type not set".

    The three typed groups are always present (an empty one shows an empty state); "Type not set" only when it has
    items. Every item lands in exactly one group, in its original order.
    """
    descriptions = descriptions or {}
    groups = [{'key': k, 'label': label, 'description': descriptions.get(k, ''), 'items': []} for k, label in TYPES]
    unset = {'key': UNSET[0], 'label': UNSET[1], 'description': 'Capabilities without a type. Set one so they join a group above.', 'items': []}
    by_key = {g['key']: g for g in groups}
    for item in items or []:
        by_key.get(type_of(item), unset)['items'].append(item)
    if unset['items']:
        groups.append(unset)
    return groups


def capability_roots(capabilities):
    """Capabilities with no parent, or whose parent is not in the data (an orphan is shown at the top, not dropped)."""
    ids = {c.get('id') for c in capabilities or []}
    return [c for c in capabilities or [] if not c.get('parentId') or c.get('parentId') not in ids]


def capability_children(capabilities, parent_id):
    return [c for c in capabilities or [] if c.get('parentId') == parent_id]


# Metric values -> step 0..5 of the ramp (0 = nothing: dashed outline, no fill).
IMPORTANCE_STEP = {'low': 1, 'medium': 2, 'high': 4, 'critical': 5}
INVESTMENT_STEP = {'none': 0, 'low': 1, 'medium': 3, 'high': 5}
MATURITY = {1: 'Initial', 2: 'Developing', 3: 'Defined', 4: 'Managed', 5: 'Optimized'}


def steps(metrics):
    m = metrics or {}
    return {'maturity': int(m.get('maturity') or 0), 'importance': IMPORTANCE_STEP.get(m.get('strategicImportance'), 0),
            'investment': INVESTMENT_STEP.get(m.get('currentInvestment'), 0)}


# One lucide icon per capability: the first keyword found in its name, else the icon of its type. Every name is in icons.ICONS.
ICON_KEYWORDS = [
    ('sustainability', 'file-bar-chart'), ('carbon', 'flame'), ('sustainable', 'globe'), ('strategy', 'target'),
    ('portfolio', 'briefcase'), ('business case', 'file-text'), ('benefit', 'trophy'), ('market intelligence', 'chart-line'),
    ('partnership', 'handshake'), ('modelling', 'chart-area'), ('hub', 'map-pin'), ('capacity', 'gauge'), ('lane', 'tag'),
    ('network', 'globe'), ('onboarding', 'user-plus'), ('customer service', 'headphones'), ('account management', 'user-check'),
    ('customer', 'users'), ('quot', 'receipt'), ('tender', 'clipboard-list'), ('sales', 'shopping-bag'), ('booking', 'calendar-check'),
    ('order', 'clipboard-list'), ('billing', 'receipt'), ('rating', 'calculator'), ('dispute', 'circle-alert'),
    ('eta', 'clock'), ('tracking', 'map-pin'), ('visibility', 'eye'), ('customs', 'landmark'), ('route', 'map'), ('load', 'container'),
    ('carrier payables', 'wallet'), ('carrier', 'truck'), ('transportation', 'truck'), ('inbound', 'arrow-down-from-line'),
    ('inventory', 'box'), ('wave', 'waves'), ('pick', 'package'), ('return', 'rotate-ccw'), ('warehouse', 'warehouse'),
    ('electrification', 'zap'), ('telematics', 'gauge'), ('maintenance', 'settings-2'), ('driver', 'user'), ('fleet', 'car'),
    ('planning & analysis', 'chart-line'), ('payroll', 'banknote'), ('accounting', 'landmark'), ('finance', 'banknote'),
    ('talent', 'user-plus'), ('training', 'book-open'), ('people', 'users'), ('integration', 'blocks'), ('master data', 'database'),
    ('analytics', 'chart-bar'), ('reporting', 'chart-pie'), ('cyber', 'shield-check'), ('cloud', 'cloud'), ('technology', 'server'),
    ('planning', 'calendar-days'), ('data', 'database'),
]
TYPE_ICON = {'strategic': 'target', 'operational': 'settings', 'supporting': 'shield', '': 'circle-help'}


def icon_for(capability):
    """The one lucide icon of a capability."""
    name = str((capability.get('name') if hasattr(capability, 'get') else '') or '').lower()
    for word, icon in ICON_KEYWORDS:
        if word in name:
            return icon
    return TYPE_ICON[type_of(capability)]
