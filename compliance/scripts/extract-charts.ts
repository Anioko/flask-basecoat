/**
 * Turns each pinned upstream chart (compliance/upstream/shadcn/charts/chart-*.tsx) into a declarative JSON spec at
 * compliance/recipes/charts/<name>.json, using the TypeScript compiler API (no evaluation of upstream code).
 *
 * Literal values (data arrays, chart configs, margins, radii...) are resolved. Function props are kept as their
 * source text and listed in `functionProps` so the runtime can map them to named formatters. Anything that is
 * neither a literal nor a function (state, derived data, computed text) becomes {"unresolved": "<source>"} and is
 * listed in `unresolved`; nothing is guessed. Schema: compliance/recipes/charts/README.md.
 *
 * Usage (from the repo root): compliance/golden/node_modules/.bin/tsx compliance/scripts/extract-charts.ts [name ...]
 */
import * as fs from "node:fs"
import * as path from "node:path"
import { createRequire } from "node:module"
import { fileURLToPath } from "node:url"

const here = path.dirname(fileURLToPath(import.meta.url))
const compliance = path.resolve(here, "..")
const require = createRequire(path.join(compliance, "golden", "package.json"))
const ts: typeof import("typescript") = require("typescript")

const srcDir = path.join(compliance, "upstream/shadcn/charts")
const outDir = path.join(compliance, "recipes/charts")
const chartsApp = path.join(compliance, "upstream/shadcn/charts-app/charts.tsx")

const CHART_TYPES: Record<string, string> = {
  AreaChart: "area",
  BarChart: "bar",
  LineChart: "line",
  PieChart: "pie",
  RadarChart: "radar",
  RadialBarChart: "radial",
}
const SERIES = new Set(["Area", "Bar", "Line", "Pie", "Radar", "RadialBar"])
const AXES = new Set(["XAxis", "YAxis", "PolarAngleAxis", "PolarRadiusAxis"])
const GRIDS = new Set(["CartesianGrid", "PolarGrid"])

const kebab = (s: string) =>
  s.replace(/Icon$/, "").replace(/([a-z0-9])([A-Z])/g, "$1-$2").replace(/([A-Z])([A-Z][a-z])/g, "$1-$2").toLowerCase()

// Grouping and fullWidth from the pinned charts page.
function readGroups() {
  const sf = ts.createSourceFile(chartsApp, fs.readFileSync(chartsApp, "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
  const out: Record<string, { group: string; fullWidth: boolean }> = {}
  const visit = (n: ts.Node, group: string | null) => {
    if (ts.isPropertyAssignment(n) && ts.isArrayLiteralExpression(n.initializer) && ts.isIdentifier(n.name)) {
      for (const el of n.initializer.elements) {
        if (!ts.isObjectLiteralExpression(el)) continue
        let id = "", full = false
        for (const p of el.properties) {
          if (!ts.isPropertyAssignment(p) || !ts.isIdentifier(p.name)) continue
          if (p.name.text === "id" && ts.isStringLiteral(p.initializer)) id = p.initializer.text
          if (p.name.text === "fullWidth") full = p.initializer.kind === ts.SyntaxKind.TrueKeyword
        }
        if (id) out[id] = { group: n.name.text, fullWidth: full }
      }
      return
    }
    ts.forEachChild(n, (c) => visit(c, group))
  }
  visit(sf, null)
  return out
}

type Ctx = {
  sf: ts.SourceFile
  top: Map<string, ts.Expression>
  local: Map<string, ts.Expression>
  state: Map<string, { state?: string; setState?: string }>
  lucide: Set<string>
  unresolved: { path: string; source: string; reason: string }[]
  functionProps: string[]
}

const text = (ctx: Ctx, n: ts.Node) => n.getText(ctx.sf).replace(/\s+/g, " ").trim()
const unwrap = (e: ts.Expression): ts.Expression => {
  while (
    ts.isParenthesizedExpression(e) || ts.isAsExpression(e) || ts.isSatisfiesExpression(e) ||
    ts.isTypeAssertionExpression(e) || ts.isNonNullExpression(e)
  ) e = e.expression
  return e
}

function unresolved(ctx: Ctx, p: string, n: ts.Node, reason: string) {
  const source = text(ctx, n)
  ctx.unresolved.push({ path: p, source, reason })
  return { unresolved: source }
}

function fnSource(ctx: Ctx, p: string, n: ts.Node) {
  ctx.functionProps.push(p)
  return text(ctx, n)
}

/** Evaluate a literal-ish expression; functions become source text; the rest is unresolved. */
function value(ctx: Ctx, e: ts.Expression, p: string, depth = 0): any {
  e = unwrap(e)
  if (ts.isStringLiteral(e) || ts.isNoSubstitutionTemplateLiteral(e)) return e.text
  if (ts.isNumericLiteral(e)) return Number(e.text)
  if (e.kind === ts.SyntaxKind.TrueKeyword) return true
  if (e.kind === ts.SyntaxKind.FalseKeyword) return false
  if (e.kind === ts.SyntaxKind.NullKeyword) return null
  if (ts.isIdentifier(e) && e.text === "undefined") return null
  if (ts.isPrefixUnaryExpression(e) && e.operator === ts.SyntaxKind.MinusToken && ts.isNumericLiteral(e.operand))
    return -Number(e.operand.text)
  if (ts.isArrayLiteralExpression(e)) return e.elements.map((x, i) => value(ctx, x, `${p}[${i}]`, depth))
  if (ts.isObjectLiteralExpression(e)) {
    const o: Record<string, any> = {}
    for (const prop of e.properties) {
      if (ts.isPropertyAssignment(prop)) {
        const k = ts.isIdentifier(prop.name) || ts.isStringLiteral(prop.name) || ts.isNumericLiteral(prop.name) ? prop.name.text : text(ctx, prop.name)
        o[k] = value(ctx, prop.initializer, `${p}.${k}`, depth)
      } else if (ts.isShorthandPropertyAssignment(prop)) {
        o[prop.name.text] = value(ctx, prop.name, `${p}.${prop.name.text}`, depth)
      } else {
        o[`...${text(ctx, prop)}`] = unresolved(ctx, p, prop, "spread or method in object literal")
      }
    }
    return o
  }
  if (ts.isArrowFunction(e) || ts.isFunctionExpression(e)) return fnSource(ctx, p, e)
  if (ts.isJsxElement(e) || ts.isJsxSelfClosingElement(e) || ts.isJsxFragment(e)) return jsx(ctx, e, p)
  if (ts.isIdentifier(e)) {
    if (ctx.lucide.has(e.text)) return { icon: kebab(e.text), component: e.text }
    // Bound to component state (useState value or setter): the runtime wires it to the control.
    if (ctx.state.has(e.text)) return ctx.state.get(e.text)
    if (ctx.top.has(e.text) && depth < 4) return value(ctx, ctx.top.get(e.text)!, p, depth + 1)
    if (ctx.local.has(e.text) && depth < 4) {
      const init = unwrap(ctx.local.get(e.text)!)
      // React.useCallback(fn, deps): the callback itself is the prop.
      if (ts.isCallExpression(init) && /useCallback$/.test(text(ctx, init.expression)) && init.arguments[0])
        return fnSource(ctx, p, init.arguments[0])
      if (ts.isStringLiteral(init) || ts.isNumericLiteral(init)) return value(ctx, init, p, depth + 1)
      return unresolved(ctx, p, e, `component-local value: ${e.text} = ${text(ctx, init)}`)
    }
  }
  return unresolved(ctx, p, e, "not a literal")
}

const tagName = (ctx: Ctx, n: ts.JsxElement | ts.JsxSelfClosingElement) =>
  text(ctx, ts.isJsxElement(n) ? n.openingElement.tagName : n.tagName)
const attrsOf = (n: ts.JsxElement | ts.JsxSelfClosingElement) =>
  (ts.isJsxElement(n) ? n.openingElement.attributes : n.attributes).properties

function props(ctx: Ctx, n: ts.JsxElement | ts.JsxSelfClosingElement, p: string, skip: string[] = []) {
  const o: Record<string, any> = {}
  for (const a of attrsOf(n)) {
    if (ts.isJsxSpreadAttribute(a)) {
      o[`...${text(ctx, a.expression)}`] = unresolved(ctx, p, a, "spread attribute")
      continue
    }
    const k = text(ctx, a.name)
    if (skip.includes(k) || k === "key") continue
    if (!a.initializer) o[k] = true
    else if (ts.isStringLiteral(a.initializer)) o[k] = a.initializer.text
    else if (ts.isJsxExpression(a.initializer) && a.initializer.expression) o[k] = value(ctx, a.initializer.expression, `${p}.${k}`)
    else if (ts.isJsxElement(a.initializer) || ts.isJsxSelfClosingElement(a.initializer)) o[k] = jsx(ctx, a.initializer, `${p}.${k}`)
  }
  return o
}

const jsxChildren = (n: ts.JsxElement | ts.JsxSelfClosingElement | ts.JsxFragment) =>
  ts.isJsxSelfClosingElement(n) ? [] : n.children.filter((c) => !(ts.isJsxText(c) && !c.text.trim()))

/** Generic JSX → {tag, props, children}; text children as strings; expressions as unresolved. */
function jsx(ctx: Ctx, n: ts.Node, p: string): any {
  if (ts.isJsxText(n)) return n.text.replace(/\s+/g, " ").trim()
  if (ts.isJsxExpression(n)) return n.expression ? value(ctx, n.expression, p) : null
  if (ts.isJsxFragment(n)) return { tag: "Fragment", children: jsxChildren(n).map((c, i) => jsx(ctx, c, `${p}.children[${i}]`)) }
  if (ts.isJsxElement(n) || ts.isJsxSelfClosingElement(n)) {
    const tag = tagName(ctx, n)
    const out: any = { tag }
    if (ctx.lucide.has(tag)) out.icon = kebab(tag)
    const pr = props(ctx, n, p)
    if (Object.keys(pr).length) out.props = pr
    const ch = jsxChildren(n)
    if (ch.length) out.children = ch.map((c, i) => jsx(ctx, c, `${p}.children[${i}]`))
    return out
  }
  return unresolved(ctx, p, n, "unsupported node")
}

function findAll(n: ts.Node, pred: (n: ts.Node) => boolean, acc: ts.Node[] = []) {
  if (pred(n)) acc.push(n)
  ts.forEachChild(n, (c) => void findAll(c, pred, acc))
  return acc
}

function findTag(ctx: Ctx, root: ts.Node, tag: string) {
  return findAll(root, (n) => (ts.isJsxElement(n) || ts.isJsxSelfClosingElement(n)) && tagName(ctx, n as any) === tag) as (
    | ts.JsxElement
    | ts.JsxSelfClosingElement
  )[]
}

/** Flattened text of a JSX element; expressions inline as {source} and recorded as unresolved. */
function flatText(ctx: Ctx, n: ts.JsxElement | ts.JsxSelfClosingElement, p: string): { text: string; icons: string[] } {
  const parts: string[] = []
  const icons: string[] = []
  const walk = (c: ts.Node) => {
    if (ts.isJsxText(c)) parts.push(c.text)
    else if (ts.isJsxExpression(c) && c.expression) {
      const v = value(ctx, c.expression, p)
      parts.push(typeof v === "string" || typeof v === "number" ? String(v) : `{${text(ctx, c.expression)}}`)
    } else if (ts.isJsxElement(c) || ts.isJsxSelfClosingElement(c)) {
      const t = tagName(ctx, c)
      if (ctx.lucide.has(t)) icons.push(kebab(t))
      else if (ts.isJsxElement(c)) c.children.forEach(walk)
    }
  }
  if (ts.isJsxElement(n)) n.children.forEach(walk)
  return { text: parts.join("").replace(/\s+/g, " ").trim(), icons }
}

function extract(name: string, groups: ReturnType<typeof readGroups>) {
  const file = path.join(srcDir, `${name}.tsx`)
  const sf = ts.createSourceFile(file, fs.readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
  const ctx: Ctx = { sf, top: new Map(), local: new Map(), state: new Map(), lucide: new Set(), unresolved: [], functionProps: [] }

  let component: ts.FunctionDeclaration | undefined
  let description: string | null = null
  for (const st of sf.statements) {
    if (ts.isImportDeclaration(st) && ts.isStringLiteral(st.moduleSpecifier) && st.moduleSpecifier.text === "lucide-react") {
      const b = st.importClause?.namedBindings
      if (b && ts.isNamedImports(b)) b.elements.forEach((e) => ctx.lucide.add(e.name.text))
    }
    if (ts.isVariableStatement(st)) {
      for (const d of st.declarationList.declarations) {
        if (ts.isIdentifier(d.name) && d.initializer) {
          ctx.top.set(d.name.text, d.initializer)
          if (d.name.text === "description" && ts.isStringLiteral(d.initializer)) description = d.initializer.text
        }
      }
    }
    if (ts.isFunctionDeclaration(st) && st.modifiers?.some((m) => m.kind === ts.SyntaxKind.ExportKeyword)) component = st
  }
  if (!component?.body) throw new Error("no exported component")

  // Component-local state and derived values.
  const state: any[] = []
  for (const st of component.body.statements) {
    if (!ts.isVariableStatement(st)) continue
    for (const d of st.declarationList.declarations) {
      if (!d.initializer) continue
      if (ts.isArrayBindingPattern(d.name)) {
        const init = unwrap(d.initializer)
        if (ts.isCallExpression(init) && /useState$/.test(text(ctx, init.expression))) {
          const [v, setter] = d.name.elements.map((x) => (ts.isBindingElement(x) ? text(ctx, x.name) : null))
          if (v) ctx.state.set(v, { state: v })
          if (setter && v) ctx.state.set(setter, { setState: v })
          const initial = init.arguments[0] ? value(ctx, init.arguments[0], `interactive.state.${v}.initial`) : null
          state.push({ name: v, setter, initial })
        }
      } else if (ts.isIdentifier(d.name)) {
        ctx.local.set(d.name.text, d.initializer)
      }
    }
  }

  const g = groups[name] || { group: name.split("-")[1], fullWidth: false }
  const spec: any = { name, group: g.group, fullWidth: g.fullWidth, description }

  // Card
  const card: any = {}
  const cardEl = findTag(ctx, component, "Card")[0]
  if (cardEl) {
    const cp = props(ctx, cardEl, "card")
    if (Object.keys(cp).length) card.props = cp
  }
  for (const [key, tag] of [["title", "CardTitle"], ["description", "CardDescription"]] as const) {
    const el = findTag(ctx, component, tag)[0]
    if (el) card[key] = flatText(ctx, el, `card.${key}`).text
  }
  for (const [key, tag] of [["header", "CardHeader"], ["content", "CardContent"]] as const) {
    const el = findTag(ctx, component, tag)[0]
    if (el) card[`${key}ClassName`] = props(ctx, el, `card.${key}`).className ?? null
  }
  const footer = findTag(ctx, component, "CardFooter")[0]
  if (footer) {
    card.footerClassName = props(ctx, footer, "card.footer").className ?? null
    // A line is an element with its own text; elements that only wrap other elements are recorded as wrappers.
    const lines: { el: ts.JsxElement | ts.JsxSelfClosingElement; wrappers: (string | null)[] }[] = []
    const isEl = (c: ts.Node): c is ts.JsxElement | ts.JsxSelfClosingElement => ts.isJsxElement(c) || ts.isJsxSelfClosingElement(c)
    const ownText = (el: ts.JsxElement | ts.JsxSelfClosingElement) => jsxChildren(el).some((c) => ts.isJsxText(c) || ts.isJsxExpression(c))
    const walkLines = (el: ts.JsxElement | ts.JsxSelfClosingElement, wrappers: (string | null)[]) => {
      for (const c of jsxChildren(el)) {
        if (!isEl(c)) continue
        if (ownText(c) || !jsxChildren(c).some(isEl)) lines.push({ el: c, wrappers })
        else walkLines(c, [...wrappers, props(ctx, c, "card.footer").className ?? null])
      }
    }
    if (ownText(footer)) lines.push({ el: footer, wrappers: [] })
    else walkLines(footer, [])
    card.footer = lines.map(({ el, wrappers }, i) => {
      const t = flatText(ctx, el, `card.footer[${i}]`)
      const line: any = { text: t.text, icons: t.icons, className: el === footer ? null : props(ctx, el, `card.footer[${i}]`).className ?? null }
      if (wrappers.length) line.wrappers = wrappers
      return line
    })
  } else card.footer = []
  spec.card = card

  // Chart
  const container = findTag(ctx, component, "ChartContainer")[0]
  if (!container) throw new Error("no ChartContainer")
  const cprops = props(ctx, container, "chart.container")
  const chartEl = jsxChildren(container).find((c) => (ts.isJsxElement(c) || ts.isJsxSelfClosingElement(c)) && CHART_TYPES[tagName(ctx, c as any)]) as
    | ts.JsxElement
    | ts.JsxSelfClosingElement
  if (!chartEl) throw new Error("no recharts chart element")
  const chartTag = tagName(ctx, chartEl)
  const chartProps = props(ctx, chartEl, "chart.props", ["data"])
  const dataAttr = attrsOf(chartEl).find((a) => ts.isJsxAttribute(a) && text(ctx, a.name) === "data") as ts.JsxAttribute | undefined
  const chart: any = {
    type: CHART_TYPES[chartTag],
    component: chartTag,
    container: { id: cprops.id ?? null, className: cprops.className ?? null },
    config: cprops.config ?? null,
    data: dataAttr?.initializer && ts.isJsxExpression(dataAttr.initializer) && dataAttr.initializer.expression
      ? value(ctx, dataAttr.initializer.expression, "chart.data")
      : null,
    props: chartProps,
    series: [] as any[],
    axes: [] as any[],
    grid: null as any,
    tooltip: null as any,
    legend: null as any,
    labels: [] as any[],
    defs: null as any,
    other: [] as any[],
  }
  if (dataAttr?.initializer && ts.isJsxExpression(dataAttr.initializer) && dataAttr.initializer.expression) {
    // Derived data: name the top-level array it is computed from, so the runtime has the rows.
    const id = unwrap(dataAttr.initializer.expression)
    if (ts.isIdentifier(id) && ctx.local.has(id.text)) {
      const refs = findAll(ctx.local.get(id.text)!, (n) => ts.isIdentifier(n) && ctx.top.has((n as ts.Identifier).text))
      const src = refs.map((r) => (r as ts.Identifier).text).find((t) => ts.isArrayLiteralExpression(unwrap(ctx.top.get(t)!)))
      if (src) chart.dataSource = { name: src, rows: value(ctx, ctx.top.get(src)!, "chart.dataSource.rows") }
    }
  }

  const nested = (el: ts.JsxElement | ts.JsxSelfClosingElement, p: string) => {
    const out: any = {}
    const kids = jsxChildren(el)
    kids.forEach((c, i) => {
      if (ts.isJsxElement(c) || ts.isJsxSelfClosingElement(c)) {
        const t = tagName(ctx, c)
        if (t === "LabelList") (out.labelList ||= []).push(props(ctx, c, `${p}.labelList[${(out.labelList || []).length}]`))
        else if (t === "Label") (out.labels ||= []).push(props(ctx, c, `${p}.labels[${(out.labels || []).length}]`))
        else (out.children ||= []).push(jsx(ctx, c, `${p}.children[${i}]`))
      } else (out.children ||= []).push(jsx(ctx, c, `${p}.children[${i}]`))
    })
    return out
  }

  jsxChildren(chartEl).forEach((c, i) => {
    if (!(ts.isJsxElement(c) || ts.isJsxSelfClosingElement(c))) {
      chart.other.push(jsx(ctx, c, `chart.other[${chart.other.length}]`))
      return
    }
    const t = tagName(ctx, c)
    if (SERIES.has(t)) {
      const p = `chart.series[${chart.series.length}]`
      chart.series.push({ component: t, ...props(ctx, c, p), ...nested(c, p) })
    } else if (AXES.has(t)) {
      const p = `chart.axes[${chart.axes.length}]`
      chart.axes.push({ component: t, ...props(ctx, c, p), ...nested(c, p) })
    } else if (GRIDS.has(t)) {
      chart.grid = { component: t, ...props(ctx, c, "chart.grid") }
    } else if (t === "ChartTooltip" || t === "ChartLegend") {
      const key = t === "ChartTooltip" ? "tooltip" : "legend"
      const own = props(ctx, c, `chart.${key}`, ["content"])
      const content = attrsOf(c).find((a) => ts.isJsxAttribute(a) && text(ctx, a.name) === "content") as ts.JsxAttribute | undefined
      let inner: any = {}
      const expr = content?.initializer && ts.isJsxExpression(content.initializer) ? content.initializer.expression && unwrap(content.initializer.expression) : undefined
      const want = t === "ChartTooltip" ? "ChartTooltipContent" : "ChartLegendContent"
      if (expr && (ts.isJsxElement(expr) || ts.isJsxSelfClosingElement(expr)) && tagName(ctx, expr) === want) {
        inner = { content: want, ...props(ctx, expr, `chart.${key}`) }
      } else if (expr) {
        inner = { content: unresolved(ctx, `chart.${key}.content`, expr, `content is not <${want} />`) }
      }
      chart[key] = { ...own, ...inner }
    } else if (t === "Label") {
      chart.labels.push(props(ctx, c, `chart.labels[${chart.labels.length}]`))
    } else if (t === "defs") {
      chart.defs = jsx(ctx, c, "chart.defs").children ?? []
    } else {
      chart.other.push(jsx(ctx, c, `chart.other[${chart.other.length}]`))
    }
  })
  if (!chart.other.length) delete chart.other
  if (!chart.defs) delete chart.defs
  spec.chart = chart

  // Interactive controls: state plus the elements that change it.
  if (state.length) {
    const controls: any[] = []
    for (const sel of findTag(ctx, component, "Select")) {
      const p = `interactive.controls[${controls.length}]`
      const sp = props(ctx, sel, p)
      const trig = findTag(ctx, sel, "SelectTrigger")[0]
      const val = findTag(ctx, sel, "SelectValue")[0]
      const content = findTag(ctx, sel, "SelectContent")[0]
      const items = findTag(ctx, sel, "SelectItem")
      const mapped = content && jsxChildren(content).some((x) => ts.isJsxExpression(x))
      controls.push({
        component: "Select",
        value: sp.value ?? null,
        onValueChange: sp.onValueChange ?? null,
        trigger: trig ? props(ctx, trig, `${p}.trigger`) : null,
        placeholder: val ? props(ctx, val, `${p}.value`).placeholder ?? null : null,
        content: content ? props(ctx, content, `${p}.content`) : null,
        items: mapped
          ? unresolved(ctx, `${p}.items`, content!, "items are built with .map() over component data")
          : items.map((it, i) => ({ ...props(ctx, it, `${p}.items[${i}]`), label: flatText(ctx, it, `${p}.items[${i}].label`).text })),
      })
    }
    const buttons = findAll(component, (n) => (ts.isJsxElement(n) || ts.isJsxSelfClosingElement(n)) && tagName(ctx, n as any) === "button")
    if (buttons.length) {
      const mapCall = findAll(component, (n) => ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.name.text === "map" && findAll(n, (m) => buttons.includes(m)).length > 0)[0]
      controls.push({
        component: "button",
        props: props(ctx, buttons[0] as any, `interactive.controls[${controls.length}].props`),
        repeat: mapCall ? unresolved(ctx, `interactive.controls[${controls.length}].repeat`, mapCall, "buttons are built with .map()") : null,
      })
    }
    const derived: Record<string, any> = {}
    for (const [k, v] of ctx.local) if (!["id"].includes(k)) derived[k] = text(ctx, v)
    spec.interactive = { state, controls, derived }
  } else spec.interactive = null

  spec.functionProps = ctx.functionProps
  spec.unresolved = ctx.unresolved
  return spec
}

const groups = readGroups()
const only = process.argv.slice(2)
fs.mkdirSync(outDir, { recursive: true })
const names = fs.readdirSync(srcDir).filter((f) => /^chart-.*\.tsx$/.test(f)).map((f) => f.replace(/\.tsx$/, "")).sort()
let ok = 0, withUnresolved = 0, failed = 0
for (const name of names) {
  if (only.length && !only.includes(name)) continue
  try {
    const spec = extract(name, groups)
    fs.writeFileSync(path.join(outDir, `${name}.json`), JSON.stringify(spec, null, 2) + "\n")
    ok++
    if (spec.unresolved.length) {
      withUnresolved++
      console.log(`${name}: ${spec.unresolved.length} unresolved (${spec.unresolved.map((u: any) => u.path).join(", ")})`)
    }
  } catch (e: any) {
    failed++
    console.log(`${name}: ERROR ${e?.message || e}`)
  }
}
console.log(`\nspecs written: ${ok}; with unresolved entries: ${withUnresolved}; failed: ${failed}`)
