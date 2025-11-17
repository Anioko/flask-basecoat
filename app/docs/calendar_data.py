"""Calendar variant data generation for docs previews."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

_WEEKDAY_LABELS_EN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
_WEEKDAY_LABELS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

_MONTH_NAMES_EN = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

_MONTH_NAMES_FR = [
    "",
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]


@dataclass(frozen=True)
class CalendarDay:
    label: int
    is_outside: bool = False
    from_next: bool = False
    is_selected: bool = False
    is_range_start: bool = False
    is_range_end: bool = False
    is_in_range: bool = False
    is_today: bool = False
    is_disabled: bool = False
    badge: Optional[str] = None
    custom: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class CalendarMonth:
    label: str
    weekday_labels: Sequence[str]
    weeks: Sequence[Sequence[CalendarDay]]
    week_numbers: Optional[Sequence[int]] = None
    time_inline: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class CalendarVariantData:
    name: str
    mode: str
    header: Dict[str, str]
    months: Sequence[CalendarMonth]
    navigation: Dict[str, bool]
    notes: Sequence[Dict[str, str]]
    presets: Sequence[str]
    inline_actions: Sequence[str]
    actions: Sequence[str]
    inputs: Sequence[Dict[str, str]]
    filters: Optional[Dict[str, Sequence[str]]]
    events: Sequence[Dict[str, str]]
    drawer: Optional[Dict[str, str]]
    brand: Optional[str]
    size: str
    columns: int
    show_week_numbers: bool
    time_picker: Optional[Dict[str, str]]
    constraint: Optional[str]
    locale: str


def _weekday_labels(start: int, locale: str = "en") -> List[str]:
    labels = list(_WEEKDAY_LABELS_FR if locale == "fr" else _WEEKDAY_LABELS_EN)
    start = start % 7
    return labels[start:] + labels[:start]


def _month_label(year: int, month: int, locale: str = "en") -> str:
    names = _MONTH_NAMES_FR if locale == "fr" else _MONTH_NAMES_EN
    return f"{names[month]} {year}"


def _ensure_date(value: Tuple[int, int, int] | date) -> date:
    if isinstance(value, date):
        return value
    year, month, day = value
    return date(year, month, day)


def _make_day(
    *,
    target: date,
    current_month: int,
    selected: Iterable[date],
    multi: Iterable[date],
    range_bounds: Optional[Tuple[date, date]],
    disabled_dates: Iterable[date],
    disabled_weekdays: Sequence[int],
    badges: Dict[date, str],
    today: Optional[date],
    custom: Dict[date, Dict[str, str]],
) -> CalendarDay:
    is_outside = target.month != current_month
    from_next = is_outside and ((target.month > current_month) or (current_month == 12 and target.month == 1))
    selected_set = set(selected)
    multi_set = set(multi)
    disabled_set = set(disabled_dates)
    badges_map = dict(badges)
    custom_map = dict(custom)

    range_start: Optional[date] = None
    range_end: Optional[date] = None
    if range_bounds:
        range_start, range_end = range_bounds

    is_selected = target in selected_set or target in multi_set
    is_range_start = range_start is not None and target == range_start
    is_range_end = range_end is not None and target == range_end
    is_in_range = False
    if range_start and range_end and range_start < target < range_end:
        is_in_range = True
    if is_range_start or is_range_end:
        is_selected = True

    is_disabled = target in disabled_set or target.weekday() in disabled_weekdays

    return CalendarDay(
        label=target.day,
        is_outside=is_outside,
        from_next=from_next,
        is_selected=is_selected,
        is_range_start=is_range_start,
        is_range_end=is_range_end,
        is_in_range=is_in_range,
        is_today=today is not None and target == today,
        is_disabled=is_disabled,
        badge=badges_map.get(target),
        custom=custom_map.get(target),
    )


def _build_month(
    year: int,
    month: int,
    *,
    locale: str = "en",
    start_of_week: int = 6,
    selected: Sequence[Tuple[int, int, int] | date] = (),
    multi: Sequence[Tuple[int, int, int] | date] = (),
    date_range: Optional[Tuple[Tuple[int, int, int] | date, Tuple[int, int, int] | date]] = None,
    disabled_dates: Sequence[Tuple[int, int, int] | date] = (),
    disabled_weekdays: Sequence[int] = (),
    badges: Dict[Tuple[int, int, int] | date, str] | None = None,
    today: Optional[Tuple[int, int, int] | date] = None,
    custom: Dict[Tuple[int, int, int] | date, Dict[str, str]] | None = None,
    show_week_numbers: bool = False,
    time_inline: Optional[Dict[str, str]] = None,
) -> CalendarMonth:
    selected_dates = [_ensure_date(value) for value in selected]
    multi_dates = [_ensure_date(value) for value in multi]
    range_bounds = None
    if date_range:
        start_value, end_value = date_range
        range_bounds = (_ensure_date(start_value), _ensure_date(end_value))
    today_value = _ensure_date(today) if today else None
    disabled_date_set = [_ensure_date(value) for value in disabled_dates]
    badge_map = {_ensure_date(key): value for key, value in (badges or {}).items()}
    custom_map = {_ensure_date(key): value for key, value in (custom or {}).items()}

    cal = calendar.Calendar(start_of_week)
    weeks: List[List[CalendarDay]] = []
    week_numbers: List[int] = []
    for week in cal.monthdatescalendar(year, month):
        if show_week_numbers:
            week_numbers.append(week[0].isocalendar()[1])
        week_days: List[CalendarDay] = []
        for day in week:
            week_days.append(
                _make_day(
                    target=day,
                    current_month=month,
                    selected=selected_dates,
                    multi=multi_dates,
                    range_bounds=range_bounds,
                    disabled_dates=disabled_date_set,
                    disabled_weekdays=tuple(disabled_weekdays),
                    badges=badge_map,
                    today=today_value,
                    custom=custom_map,
                )
            )
        weeks.append(week_days)

    weekday_labels = _weekday_labels(start_of_week, locale)
    label = _month_label(year, month, locale)

    return CalendarMonth(
        label=label,
        weekday_labels=weekday_labels,
        weeks=weeks,
        week_numbers=week_numbers if show_week_numbers else None,
        time_inline=time_inline,
    )


def _default_notes() -> List[Dict[str, str]]:
    return [
        {"label": "Deep work sprint", "meta": "Oct 12 – Oct 16"},
        {"label": "Product sync", "meta": "Tue, Oct 14 • 10:30"},
    ]


BASE_YEAR = 2025
BASE_MONTH = 10
NEXT_MONTH = 11

BASE_TODAY = date(2025, 10, 14)
BASE_SELECTED = date(2025, 10, 12)
BASE_MULTI = [date(2025, 10, 4), date(2025, 10, 11), date(2025, 10, 18), date(2025, 10, 25)]
BASE_RANGE = (date(2025, 10, 11), date(2025, 10, 16))
CROSS_RANGE = (date(2025, 10, 28), date(2025, 11, 4))

DEFAULT_HEADER = {
    "title": "Team availability",
    "subtitle": "Coordinate product milestones in one view.",
}


def _variant_defaults(name: str, blueprint: Dict[str, object]) -> Dict[str, object]:
    months = _build_months(blueprint.get("months", ()))
    layout_columns = blueprint.get("columns") or len(months)

    data: Dict[str, object] = {
        "name": name,
        "mode": blueprint.get("mode", "single"),
        "header": {**DEFAULT_HEADER, **blueprint.get("header", {})},
        "months": [
            {
                "label": month.label,
                "weekday_labels": list(month.weekday_labels),
                "weeks": [
                    [
                        {
                            "label": day.label,
                            "is_outside": day.is_outside,
                            "from_next": day.from_next,
                            "is_selected": day.is_selected,
                            "is_range_start": day.is_range_start,
                            "is_range_end": day.is_range_end,
                            "is_in_range": day.is_in_range,
                            "is_today": day.is_today,
                            "is_disabled": day.is_disabled,
                            "badge": day.badge,
                            "custom": day.custom,
                        }
                        for day in week
                    ]
                    for week in month.weeks
                ],
                "week_numbers": list(month.week_numbers) if month.week_numbers else [],
                "time_inline": month.time_inline,
            }
            for month in months
        ],
        "navigation": blueprint.get("navigation", {}),
        "notes": list(blueprint.get("notes", [])),
        "presets": list(blueprint.get("presets", [])),
        "inline_actions": list(blueprint.get("inline_actions", [])),
        "actions": list(blueprint.get("actions", [])),
        "inputs": list(blueprint.get("inputs", [])),
        "filters": blueprint.get("filters"),
        "events": list(blueprint.get("events", [])),
        "drawer": blueprint.get("drawer"),
        "brand": blueprint.get("brand"),
        "size": blueprint.get("size", "standard"),
        "columns": layout_columns,
        "show_week_numbers": bool(blueprint.get("show_week_numbers", False)),
        "time_picker": blueprint.get("time_picker"),
        "constraint": blueprint.get("constraint"),
        "locale": blueprint.get("locale", "en"),
    }
    return data


def build_calendar_variant(name: str) -> Dict[str, object]:
    blueprint = _VARIANT_BLUEPRINTS.get(name)
    if not blueprint:
        raise KeyError(f"Unknown calendar variant: {name}")
    return _variant_defaults(name, blueprint)


def all_calendar_variant_data() -> Dict[str, Dict[str, object]]:
    return {name: build_calendar_variant(name) for name in _VARIANT_BLUEPRINTS.keys()}


def _month_cfg(
    year: int,
    month: int,
    *,
    locale: str = "en",
    start_of_week: int = 6,
    selected: Sequence[Tuple[int, int, int] | date] = (),
    multi: Sequence[Tuple[int, int, int] | date] = (),
    date_range: Optional[Tuple[Tuple[int, int, int] | date, Tuple[int, int, int] | date]] = None,
    disabled_dates: Sequence[Tuple[int, int, int] | date] = (),
    disabled_weekdays: Sequence[int] = (),
    badges: Dict[Tuple[int, int, int] | date, str] | None = None,
    today: Optional[Tuple[int, int, int] | date] = None,
    custom: Dict[Tuple[int, int, int] | date, Dict[str, str]] | None = None,
    show_week_numbers: bool = False,
    time_inline: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    return {
        "year": year,
        "month": month,
        "locale": locale,
        "start_of_week": start_of_week,
        "selected": selected,
        "multi": multi,
        "date_range": date_range,
        "disabled_dates": disabled_dates,
        "disabled_weekdays": disabled_weekdays,
        "badges": badges,
        "today": today,
        "custom": custom,
        "show_week_numbers": show_week_numbers,
        "time_inline": time_inline,
    }


def _build_months(configs: Sequence[Dict[str, object]]) -> List[CalendarMonth]:
    months: List[CalendarMonth] = []
    for cfg in configs:
        months.append(
            _build_month(
                cfg["year"],
                cfg["month"],
                locale=cfg.get("locale", "en"),
                start_of_week=cfg.get("start_of_week", 6),
                selected=cfg.get("selected", ()),
                multi=cfg.get("multi", ()),
                date_range=cfg.get("date_range"),
                disabled_dates=cfg.get("disabled_dates", ()),
                disabled_weekdays=cfg.get("disabled_weekdays", ()),
                badges=cfg.get("badges"),
                today=cfg.get("today"),
                custom=cfg.get("custom"),
                show_week_numbers=cfg.get("show_week_numbers", False),
                time_inline=cfg.get("time_inline"),
            )
        )
    return months


_VARIANT_BLUEPRINTS: Dict[str, Dict[str, object]] = {
    "calendar-01": {
        "mode": "single",
        "header": {"meta": "Single date selection"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(
                BASE_YEAR,
                BASE_MONTH,
                selected=[BASE_SELECTED],
                today=BASE_TODAY,
            )
        ],
        "notes": _default_notes(),
    },
    "calendar-02": {
        "mode": "single",
        "header": {"meta": "Single selection • Two months"},
        "navigation": {"chevrons": True},
        "columns": 2,
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
            _month_cfg(BASE_YEAR, NEXT_MONTH),
        ],
    },
    "calendar-03": {
        "mode": "multi",
        "header": {"meta": "Multiple dates"},
        "navigation": {"chevrons": True},
        "columns": 2,
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, multi=BASE_MULTI, today=BASE_TODAY),
            _month_cfg(BASE_YEAR, NEXT_MONTH, multi=[date(2025, 11, 2), date(2025, 11, 9)]),
        ],
    },
    "calendar-04": {
        "mode": "range",
        "header": {"meta": "Date range"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, date_range=BASE_RANGE, today=BASE_TODAY),
        ],
    },
    "calendar-05": {
        "mode": "range",
        "header": {"meta": "Range across months"},
        "inline_actions": ["Clear", "Apply"],
        "navigation": {"chevrons": True},
        "columns": 2,
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, date_range=CROSS_RANGE),
            _month_cfg(BASE_YEAR, NEXT_MONTH, date_range=CROSS_RANGE),
        ],
    },
    "calendar-06": {
        "mode": "range",
        "header": {"meta": "Range with minimum"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, date_range=BASE_RANGE),
        ],
        "constraint": "Stay at least 3 nights.",
    },
    "calendar-07": {
        "mode": "range",
        "header": {"meta": "Range with min & max"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, date_range=BASE_RANGE),
        ],
        "constraint": "Stay 3–10 nights.",
    },
    "calendar-08": {
        "mode": "single",
        "header": {"meta": "Disabled days"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(
                BASE_YEAR,
                BASE_MONTH,
                selected=[BASE_SELECTED],
                disabled_dates=[date(2025, 10, 5), date(2025, 10, 19)],
                today=BASE_TODAY,
            )
        ],
    },
    "calendar-09": {
        "mode": "single",
        "header": {"meta": "Disabled weekends"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(
                BASE_YEAR,
                BASE_MONTH,
                selected=[BASE_SELECTED],
                disabled_weekdays=[5, 6],
                today=BASE_TODAY,
            )
        ],
    },
    "calendar-10": {
        "mode": "single",
        "header": {"meta": "Today shortcut"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "inline_actions": ["Today"],
    },
    "calendar-11": {
        "mode": "single",
        "header": {"meta": "Start / End"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "inline_actions": ["Start", "End"],
    },
    "calendar-12": {
        "mode": "single",
        "header": {"meta": "Français"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(
                BASE_YEAR,
                BASE_MONTH,
                locale="fr",
                start_of_week=0,
                selected=[BASE_SELECTED],
                today=BASE_TODAY,
            )
        ],
        "locale": "fr",
    },
    "calendar-13": {
        "mode": "single",
        "header": {"meta": "Month dropdown"},
        "navigation": {"chevrons": True, "dropdowns": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
    },
    "calendar-14": {
        "mode": "single",
        "header": {"meta": "Booked days"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(
                BASE_YEAR,
                BASE_MONTH,
                selected=[BASE_SELECTED],
                badges={date(2025, 10, 6): "Booked", date(2025, 10, 17): "Booked"},
                today=BASE_TODAY,
            )
        ],
    },
    "calendar-15": {
        "mode": "single",
        "header": {"meta": "Week numbers"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(
                BASE_YEAR,
                BASE_MONTH,
                selected=[BASE_SELECTED],
                today=BASE_TODAY,
                show_week_numbers=True,
            )
        ],
        "show_week_numbers": True,
    },
    "calendar-16": {
        "mode": "single",
        "header": {"meta": "Time picker"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "time_picker": {"label": "Time", "value": "14:00"},
    },
    "calendar-17": {
        "mode": "single",
        "header": {"meta": "Inline time"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(
                BASE_YEAR,
                BASE_MONTH,
                selected=[BASE_SELECTED],
                today=BASE_TODAY,
                time_inline={"label": "Time", "value": "09:30"},
            )
        ],
    },
    "calendar-18": {
        "mode": "single",
        "header": {"meta": "Compact"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "size": "compact",
    },
    "calendar-19": {
        "mode": "single",
        "header": {"meta": "Presets"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "presets": ["Last 7 days", "Last 30 days", "This quarter"],
    },
    "calendar-20": {
        "mode": "single",
        "header": {"meta": "Presets + time"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "presets": ["Last 7 days", "Last 30 days", "Custom"],
        "time_picker": {"label": "Time", "value": "08:30"},
    },
    "calendar-21": {
        "mode": "single",
        "header": {"meta": "Custom render"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(
                BASE_YEAR,
                BASE_MONTH,
                selected=[BASE_SELECTED],
                today=BASE_TODAY,
                custom={
                    date(2025, 10, 15): {"label": "Launch", "tone": "success"},
                    date(2025, 10, 22): {"label": "Offsite", "tone": "info"},
                },
            )
        ],
    },
    "calendar-22": {
        "mode": "picker",
        "header": {"meta": "Date picker"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "inputs": [{"label": "Selected date", "value": "Oct 12, 2025"}],
    },
    "calendar-23": {
        "mode": "range-picker",
        "header": {"meta": "Range picker"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, date_range=BASE_RANGE, today=BASE_TODAY),
        ],
        "inputs": [
            {"label": "Start", "value": "Oct 11, 2025"},
            {"label": "End", "value": "Oct 16, 2025"},
        ],
    },
    "calendar-24": {
        "mode": "picker",
        "header": {"meta": "Date & time"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "inputs": [{"label": "Date & time", "value": "Oct 12, 2025 · 14:00"}],
    },
    "calendar-25": {
        "mode": "range-picker",
        "header": {"meta": "Range & time"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, date_range=BASE_RANGE),
        ],
        "inputs": [
            {"label": "Start", "value": "Oct 11, 2025 · 09:00"},
            {"label": "End", "value": "Oct 16, 2025 · 17:00"},
        ],
    },
    "calendar-26": {
        "mode": "range",
        "header": {"meta": "Range + time"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, date_range=BASE_RANGE),
        ],
        "time_picker": {"label": "Time", "value": "All day"},
    },
    "calendar-27": {
        "mode": "filter",
        "header": {"meta": "Filters"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "filters": {"label": "Breakdown", "options": ["Revenue", "Sessions", "Customers"]},
    },
    "calendar-28": {
        "mode": "input",
        "header": {"meta": "Input field"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "inputs": [{"label": "Date", "value": "Oct 12, 2025"}],
    },
    "calendar-29": {
        "mode": "natural",
        "header": {"meta": "Natural language"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, date_range=BASE_RANGE),
        ],
        "inputs": [{"label": "Natural input", "value": "next tuesday to next friday"}],
    },
    "calendar-30": {
        "mode": "single",
        "header": {"meta": "little-date"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "brand": "little-date",
    },
    "calendar-31": {
        "mode": "events",
        "header": {"meta": "Event slots"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "events": [
            {"title": "Product release", "meta": "09:00 • Engineering"},
            {"title": "Customer briefing", "meta": "13:30 • Sales"},
        ],
    },
    "calendar-32": {
        "mode": "drawer",
        "header": {"meta": "Drawer"},
        "navigation": {"chevrons": True},
        "months": [
            _month_cfg(BASE_YEAR, BASE_MONTH, selected=[BASE_SELECTED], today=BASE_TODAY),
        ],
        "drawer": {
            "title": "Pick dates",
            "copy": "Render this calendar within a drawer component.",
            "cta": "Confirm selection",
        },
        "inputs": [{"label": "Selected dates", "value": "Oct 11 – Oct 16, 2025"}],
    },
}