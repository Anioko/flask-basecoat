## Strategy canvases (Tier C)

Not shadcn components: library macros that compose them. Import the barrel and pass the content as data:

```jinja
{% import 'basecoat/canvas/index.html' as canvas %}
{{ canvas.swot_analysis(data) }}
```

Every canvas macro takes `data` and `id=<slug>`. The framework's wording and layout are constants of the macro; the content is data
(`flask_basecoat/data/canvases/<slug>.json`, Northwind Logistics). Each draws ONE region marked `data-entelim-form="<form>"`: a
focusable named `role="region"` with `overflow-x-auto` that keeps the form's natural width (a phone scrolls sideways, it never
stacks), plus a "... view" ToggleGroup and a Table as the accessible route. Note boxes are editable through one Sheet (Field and
Textarea, one note per line). Page: `/examples/canvas/<slug>`; check it with
`python compliance/scripts/check_page.py /examples/canvas/<slug> --nearest dashboard-01` (a page with a marked region is also held to the Tier C `form` conditions).

| Macro | Form | Data |
|---|---|---|
| `canvas.business_model_canvas` | C4 | `boxes`: key-partners key-activities key-resources value-propositions customer-relationships channels customer-segments cost-structure revenue-streams |
| `canvas.lean_canvas` | C4 | `boxes`: problem existing-alternatives solution key-metrics unique-value-proposition high-level-concept unfair-advantage channels customer-segments early-adopters cost-structure revenue-streams |
| `canvas.value_proposition_canvas` | C4 | `boxes` for the Value Map (products-services, pain-relievers, gain-creators) and Customer Profile (customer-jobs, pains, gains) |
| `canvas.empathy_map` | C4 | `boxes` (user, says, thinks, does, feels, pains, gains) |
| `canvas.product_vision_board` | C4 | `boxes` (vision, target-group, needs, product, business-goals) |
| `canvas.swot_analysis`, `pestle_analysis`, `ansoff_matrix`, `porters_five_forces`, `mckinsey_7s` | C2 | `boxes` keyed by the framework's boxes |
| `canvas.balanced_scorecard` | C2 | `vision`, `strategy`, `perspectives` (objective, measure, target, initiative rows) |
| `canvas.okr` | C2 | `objectives` with key results (`start`, `current`, `target`; score is derived) |
| `canvas.blue_ocean` | C2 | `companies`, `factors` (scores 0 to 10), `actions` (eliminate, reduce, raise, create); the value curves are a `ui.chart_from_spec` line chart |
| `canvas.wardley_mapping` | C1 | `components` (evolution and visibility 0 to 1, `depends_on`, `movement`) |

The exact box keys of each canvas are in its example data file.

## Capability map (capability_type)

```jinja
{% import 'basecoat/capability_map/index.html' as capmap %}
{{ capmap.capability_map(data) }}
```

`data` = `{'map': {name, description, typeDescriptions}, 'capabilities': [...], 'applications': [...]}`. Each capability carries
`capability_type` (strategic, operational or supporting) and is grouped by that field only, in that order, each group under a heading;
an empty or unknown value goes in a final group "Type not set" and is never dropped. Roots with their sub-capabilities nest inside
their group; the helpers are `flask_basecoat.capability` (`capability_groups`, `capability_roots`, `capability_children`), also Jinja globals.
Heat is one ramp of the primary token at 20, 40, 60, 80 and 100 percent (`bg-primary/20` ... `bg-primary`; step 0 is a dashed outline),
shown as a swatch or bar beside the figure in words. `python scripts/capability_ramp.py` prints the OKLab distances.

| Macro | Page | Form |
|---|---|---|
| `capmap.capability_map` | `/examples/capability/capability-map` | C2, levelled heat map, "Heat by" ToggleGroup, legend Badges, detail Sheet, list route |
| `capmap.capability_tree` | `/examples/capability/capability-tree` | C2, indented tree with disclosure buttons, Table view |
| `capmap.applications_by_capability` | `/examples/capability/applications-by-capability` | C2, one Table, row groups per type, "Coverage view" filter |
| `capmap.capability_planning` | `/examples/capability/capability-planning` | Tier B, four section cards and the gap Table |
| `capmap.form_dialog`, `metadata_dialog`, `type_dialog`, `delete_dialog` | `/examples/capability/capability-dialogs` | Tier B, the four dialogs; saving emits `basecoat:capability-save` and `basecoat:capability-delete`, nothing is stored |
