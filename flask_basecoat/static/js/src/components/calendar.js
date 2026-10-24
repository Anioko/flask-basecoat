/* Calendar: renders the month grid the way react-day-picker renders it for shadcn (same classes and
   attributes as the upstream markup), with single, multiple and range selection, month navigation,
   month/year dropdowns when data-caption-layout="dropdown", week numbers and outside days.
   Configure through data attributes on [data-slot="calendar"]:
     data-mode="single|multiple|range" data-selected="2026-10-12" (comma separated / "start,end" for range)
     data-month="2026-10" data-number-of-months="2" data-week-starts-on="0" data-min / data-max (ISO dates)
     data-name="field" (hidden input name) data-caption-layout="label|dropdown" data-show-week-numbers
   A calendar rendered by the server already containing a grid is left alone until the user navigates. */
(function (FB) {
  'use strict';

  const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  // react-day-picker's month dropdown (options and caption) uses the short en-US month names.
  const MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const pad = (n) => String(n).padStart(2, '0');
  const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const ddmmyyyy = (d) => `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
  // ISO yyyy-mm-dd only; anything else (an empty or partial value) is no date, so callers fall back to their default.
  const parse = (s) => { const m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(String(s || '').trim()); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; };
  const same = (a, b) => a && b && a.getTime() === b.getTime();
  const ordinal = (n) => n + (n % 10 === 1 && n !== 11 ? 'st' : n % 10 === 2 && n !== 12 ? 'nd' : n % 10 === 3 && n !== 13 ? 'rd' : 'th');
  const CHEV = { left: '<path d="m15 18-6-6 6-6"/>', right: '<path d="m9 18 6-6-6-6"/>', down: '<path d="m6 9 6 6 6-6"/>' };
  const svg = (dir, cls, size) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size || 24}" height="${size || 24}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-${dir} ${cls}" aria-hidden="true">${CHEV[dir]}</svg>`;
  const BTN = 'cn-button group/button inline-flex shrink-0 items-center justify-center whitespace-nowrap transition-all outline-none select-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0';
  const DAY_BTN = `${BTN} cn-button-variant-ghost cn-button-size-icon cn-calendar-day-button relative isolate z-10 flex aspect-square size-auto w-full min-w-(--cell-size) flex-col gap-1 border-0 leading-none font-normal group-data-[focused=true]/day:relative group-data-[focused=true]/day:z-10 group-data-[focused=true]/day:border-ring group-data-[focused=true]/day:ring-[3px] group-data-[focused=true]/day:ring-ring/50 data-[range-end=true]:rounded-(--cell-radius) data-[range-end=true]:rounded-r-(--cell-radius) data-[range-end=true]:bg-primary data-[range-end=true]:text-primary-foreground data-[range-middle=true]:rounded-none data-[range-middle=true]:bg-muted data-[range-middle=true]:text-foreground data-[range-start=true]:rounded-(--cell-radius) data-[range-start=true]:rounded-l-(--cell-radius) data-[range-start=true]:bg-primary data-[range-start=true]:text-primary-foreground data-[selected-single=true]:bg-primary data-[selected-single=true]:text-primary-foreground dark:hover:text-foreground [&>span]:text-xs [&>span]:opacity-70`;
  const DAY_CELL = "group/day relative aspect-square h-full w-full rounded-(--cell-radius) p-0 text-center select-none [&:last-child[data-selected=true]_button]:rounded-r-(--cell-radius) [&:first-child[data-selected=true]_button]:rounded-l-(--cell-radius) rdp-day";

  FB.register('calendar', {
    init(root) {
      const mode = root.getAttribute('data-mode') || 'single';
      const months = Number(root.getAttribute('data-number-of-months') || 1);
      const weekStart = Number(root.getAttribute('data-week-starts-on') || 0);
      const showWeeks = root.hasAttribute('data-show-week-numbers') || root.getAttribute('data-week-numbers') === 'true';
      const dropdown = root.getAttribute('data-caption-layout') === 'dropdown';
      const min = parse(root.getAttribute('data-min')), max = parse(root.getAttribute('data-max'));
      const name = root.getAttribute('data-name');
      let selected = (root.getAttribute('data-selected') || '').split(',').filter(Boolean).map(parse);
      let range = mode === 'range' ? { from: selected[0] || null, to: selected[1] || null } : null;
      let view = parse((root.getAttribute('data-month') || '') + '-01') || selected[0] || new Date();
      view = new Date(view.getFullYear(), view.getMonth(), 1);
      let hidden = null;
      if (name) { hidden = document.createElement('input'); hidden.type = 'hidden'; hidden.name = name; root.appendChild(hidden); }
      const prerendered = !!FB.qs(root, '.rdp-months');
      if (prerendered && !root.hasAttribute('data-live')) {
        // Static server markup: only wire navigation and selection on top of it.
        root.setAttribute('data-live', '');
      }

      function isSelected(d) {
        if (mode === 'range') return range.from && (same(d, range.from) || same(d, range.to) || (range.to && d > range.from && d < range.to));
        return selected.some((s) => same(s, d));
      }
      function monthGrid(first) {
        const y = first.getFullYear(), m = first.getMonth();
        const start = new Date(y, m, 1);
        const offset = (start.getDay() - weekStart + 7) % 7;
        const gridStart = new Date(y, m, 1 - offset);
        const weeks = [];
        for (let w = 0; w < 6; w++) {
          const days = [];
          for (let i = 0; i < 7; i++) days.push(new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + w * 7 + i));
          if (w >= 4 && days[0].getMonth() !== m) break;
          weeks.push(days);
        }
        return weeks;
      }
      function weekNumber(d) {
        const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
        const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);
        const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
        return Math.ceil(((t - y0) / 86400000 + 1) / 7);
      }
      function render() {
        const today = new Date(); today.setHours(0, 0, 0, 0);
        const monthsHtml = [];
        for (let k = 0; k < months; k++) {
          const first = new Date(view.getFullYear(), view.getMonth() + k, 1);
          const label = `${MONTHS[first.getMonth()]} ${first.getFullYear()}`;
          const caption = dropdown
            ? `<div class="flex h-(--cell-size) w-full items-center justify-center gap-1.5 text-sm font-medium rdp-dropdowns">
                 <span data-disabled="false" class="cn-calendar-dropdown-root relative rounded-(--cell-radius) rdp-dropdown_root"><select aria-label="Choose the Month" data-fb-month class="absolute inset-0 bg-popover opacity-0 rdp-dropdown rdp-months_dropdown">${MONTHS_SHORT.map((mn, i) => `<option value="${i}"${i === first.getMonth() ? ' selected' : ''}>${mn}</option>`).join('')}</select><span aria-hidden="true" class="font-medium select-none cn-calendar-caption-label flex items-center gap-1 rounded-(--cell-radius) text-sm [&>svg]:size-3.5 [&>svg]:text-muted-foreground rdp-caption_label">${MONTHS_SHORT[first.getMonth()]}${svg('down', 'size-4 rdp-chevron', 18)}</span></span>
                 <span data-disabled="false" class="cn-calendar-dropdown-root relative rounded-(--cell-radius) rdp-dropdown_root"><select aria-label="Choose the Year" data-fb-year class="absolute inset-0 bg-popover opacity-0 rdp-dropdown rdp-years_dropdown">${Array.from({ length: 101 }, (_, i) => first.getFullYear() - 100 + i + 50).filter((yy) => yy >= 1926 && yy <= 2100).map((yy) => `<option value="${yy}"${yy === first.getFullYear() ? ' selected' : ''}>${yy}</option>`).join('')}</select><span aria-hidden="true" class="font-medium select-none cn-calendar-caption-label flex items-center gap-1 rounded-(--cell-radius) text-sm [&>svg]:size-3.5 [&>svg]:text-muted-foreground rdp-caption_label">${first.getFullYear()}${svg('down', 'size-4 rdp-chevron', 18)}</span></span>
               </div>`
            : `<span class="font-medium select-none cn-calendar-caption-label flex items-center gap-1 rounded-(--cell-radius) text-sm [&>svg]:size-3.5 [&>svg]:text-muted-foreground rdp-caption_label" role="status" aria-live="polite">${label}</span>`;
          const weekdays = Array.from({ length: 7 }, (_, i) => DAYS[(i + weekStart) % 7]);
          const rows = monthGrid(first).map((week) => {
            const cells = week.map((d) => {
              const outside = d.getMonth() !== first.getMonth();
              const disabled = (min && d < min) || (max && d > max);
              const sel = !!isSelected(d);
              const rs = mode === 'range' && range.from && same(d, range.from), re = mode === 'range' && range.to && same(d, range.to);
              const rm = mode === 'range' && range.from && range.to && d > range.from && d < range.to;
              const single = sel && mode !== 'range';
              const attrs = [`role="gridcell"`, `data-day="${iso(d)}"`, `data-month="${iso(first).slice(0, 7)}"`,
                outside ? 'data-outside="true"' : '', sel ? 'aria-selected="true" data-selected="true"' : '', same(d, today) ? 'data-today="true"' : '', disabled ? 'data-disabled="true" aria-disabled="true"' : ''];
              const btnAttrs = [`data-slot="button"`, `data-variant="ghost"`, `data-size="icon"`, `data-day="${ddmmyyyy(d)}"`, single ? 'data-selected-single="true"' : '',
                mode === 'range' ? `data-range-start="${!!rs}" data-range-end="${!!re}" data-range-middle="${!!rm}"` : '', 'type="button"', `tabindex="${sel ? 0 : -1}"`,
                `aria-label="${DAYS[d.getDay()]}, ${MONTHS[d.getMonth()]} ${ordinal(d.getDate())}, ${d.getFullYear()}${sel ? ', selected' : ''}"`, disabled ? 'disabled' : ''];
              return `<td ${attrs.join(' ')} class="${DAY_CELL}"><button ${btnAttrs.join(' ')} class="${DAY_BTN}">${d.getDate()}</button></td>`;
            }).join('');
            const wk = showWeeks ? `<td class="text-[0.8rem] text-muted-foreground select-none rdp-week_number"><div class="flex size-(--cell-size) items-center justify-center text-center">${weekNumber(week[0])}</div></td>` : '';
            return `<tr class="mt-2 flex w-full rdp-week">${wk}${cells}</tr>`;
          }).join('');
          monthsHtml.push(`<div class="flex w-full flex-col gap-4 rdp-month">
            <div class="flex h-(--cell-size) w-full items-center justify-center px-(--cell-size) rdp-month_caption">${caption}</div>
            <table role="grid" aria-multiselectable="${mode !== 'single'}" aria-label="${label}" class="w-full border-collapse rdp-month_grid">
              <thead aria-hidden="true"><tr class="flex rdp-weekdays">${showWeeks ? '<th class="w-(--cell-size) select-none rdp-week_number_header"></th>' : ''}${weekdays.map((wd) => `<th aria-label="${wd}" scope="col" class="flex-1 rounded-(--cell-radius) text-[0.8rem] font-normal text-muted-foreground select-none rdp-weekday">${wd.slice(0, 2)}</th>`).join('')}</tr></thead>
              <tbody class="rdp-weeks">${rows}</tbody>
            </table></div>`);
        }
        root.innerHTML = `<div class="relative flex flex-col gap-4 md:flex-row rdp-months">
          <nav aria-label="Navigation bar" class="absolute inset-x-0 top-0 flex w-full items-center justify-between gap-1 rdp-nav">
            <button type="button" data-fb-prev aria-label="Go to the Previous Month" class="${BTN} cn-button-variant-ghost cn-button-size-icon-sm cn-calendar-nav-button aria-disabled:opacity-50 rdp-button_previous">${svg('left', 'cn-rtl-flip size-4 rdp-chevron')}</button>
            <button type="button" data-fb-next aria-label="Go to the Next Month" class="${BTN} cn-button-variant-ghost cn-button-size-icon-sm cn-calendar-nav-button aria-disabled:opacity-50 rdp-button_next">${svg('right', 'cn-rtl-flip size-4 rdp-chevron')}</button>
          </nav>${monthsHtml.join('')}</div>`;
        if (hidden) {
          root.appendChild(hidden);
          hidden.value = mode === 'range' ? [range.from, range.to].filter(Boolean).map(iso).join(',') : selected.map(iso).join(',');
        }
        root.setAttribute('data-month', iso(view).slice(0, 7));
      }
      function select(d) {
        if (mode === 'single') selected = same(selected[0], d) && root.hasAttribute('data-deselectable') ? [] : [d];
        else if (mode === 'multiple') { const i = selected.findIndex((s) => same(s, d)); if (i >= 0) selected.splice(i, 1); else selected.push(d); }
        else {
          if (!range.from || (range.from && range.to)) range = { from: d, to: null };
          else if (d < range.from) range = { from: d, to: range.from };
          else range.to = d;
        }
        render();
        FB.emit(root, 'change', { value: mode === 'range' ? { from: range.from && iso(range.from), to: range.to && iso(range.to) } : selected.map(iso) });
      }
      root.addEventListener('click', (e) => {
        const prev = e.target.closest('[data-fb-prev], .rdp-button_previous'), next = e.target.closest('[data-fb-next], .rdp-button_next');
        if (prev) { view = new Date(view.getFullYear(), view.getMonth() - 1, 1); render(); return; }
        if (next) { view = new Date(view.getFullYear(), view.getMonth() + 1, 1); render(); return; }
        const cell = e.target.closest('td[data-day]');
        if (cell && !cell.hasAttribute('data-disabled')) select(parse(cell.getAttribute('data-day')));
      });
      root.addEventListener('change', (e) => {
        if (e.target.matches('[data-fb-month]')) { view = new Date(view.getFullYear(), Number(e.target.value), 1); render(); }
        if (e.target.matches('[data-fb-year]')) { view = new Date(Number(e.target.value), view.getMonth(), 1); render(); }
      });
      root.addEventListener('keydown', (e) => {
        const btn = e.target.closest('td[data-day] button');
        if (!btn) return;
        const d = parse(btn.closest('td').getAttribute('data-day'));
        const delta = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[e.key];
        if (delta) {
          e.preventDefault();
          const n = new Date(d.getFullYear(), d.getMonth(), d.getDate() + delta);
          if (n.getMonth() !== view.getMonth() && months === 1) { view = new Date(n.getFullYear(), n.getMonth(), 1); render(); }
          const target = FB.qs(root, `td[data-day="${iso(n)}"] button`);
          if (target) { target.focus(); target.closest('td').setAttribute('data-focused', 'true'); }
        } else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(d); }
      });
      if (!prerendered || root.hasAttribute('data-render')) render();
      root.fbRender = render; root.fbSelect = select;
    },
  });
})(window.FlaskBasecoat);
