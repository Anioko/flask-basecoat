/**
 * Browser golden for the shadcn charts.
 * Recharts measures its parent with a ResizeObserver, so the charts only exist after a real layout pass.
 * This entry runs in headless Chromium (driven by render_charts.py), renders one upstream chart (or the
 * `chart` component example) with createRoot, and flags `window.__ready` once every chart surface has a size.
 *
 * ?name=chart-area-default   one of the 70 charts, inside the upstream ComponentPreview wrapper at the canonical width
 * ?name=chart                the radix `chart` component example, exactly as the SSR goldens place examples
 * ?name=blocks/dashboard-01   the dashboard-01 block's ChartAreaInteractive card, at the width the block gives it
 */
import * as React from "react"
import { createRoot } from "react-dom/client"

import { charts } from "../../upstream/shadcn/charts-app/charts"
import { ComponentPreview } from "../../upstream/shadcn/charts-app/view-component-preview"
import { extraCharts } from "./extra/charts"
import ChartExample from "../../upstream/shadcn/radix/examples/chart-example"
import { ChartAreaInteractive as Dashboard01Chart } from "../../upstream/shadcn/radix/blocks/dashboard-01/components/chart-area-interactive"

// Canonical widths: the upstream charts page is a 3-column grid; at a 1280px viewport one column is 384px
// and a full-width chart (md:col-span-2 lg:col-span-3) spans 1232px. Shared with our pages (see CONVENTIONS.md).
export const REGULAR_WIDTH = 384
export const FULL_WIDTH = 1232

// Charts that live inside a block. The width is the width of the card in the block's own layout at the 1440x900
// viewport the block checks use, measured on the block page (dashboard-01: 1440 - sidebar 288 - inset margin 8 -
// px-6 24 on both sides = 1096; the chart container inside the card's px-6 content is 1048 wide, 250 high).
export const BLOCK_CHARTS: Record<string, { component: React.ComponentType; width: number }> = {
  "blocks/dashboard-01": { component: Dashboard01Chart, width: 1096 },
}

type Item = { id: string; component: React.ComponentType; fullWidth?: boolean }

const index: Record<string, { group: string; item: Item }> = {}
for (const [group, items] of Object.entries(charts as Record<string, Item[]>)) {
  for (const item of items) index[item.id] = { group, item }
}

declare global {
  interface Window {
    __ready?: boolean
    __error?: string
    __chart?: { name: string; group: string | null; fullWidth: boolean; width: number | null }
    __charts?: Record<string, { group: string; fullWidth: boolean }>
    __extraCharts?: Record<string, { group: string; width: number }>
  }
}

// Charts for the forms shadcn has no original for (R18, R19): ?name=<chart> finds them in ./extra/charts.tsx.
// They are not part of window.__charts, so the 70-chart run is unchanged; `render_charts.py --extra` takes them.
window.__extraCharts = Object.fromEntries(
  Object.entries(extraCharts).map(([id, e]) => [id, { group: e.group, width: e.width }])
)

window.__charts = Object.fromEntries(
  Object.entries(index).map(([id, { group, item }]) => [id, { group, fullWidth: !!item.fullWidth }])
)

const name = new URLSearchParams(location.search).get("name") || ""
const root = document.getElementById("root")!

function element(): React.ReactElement | null {
  if (name === "chart") {
    window.__chart = { name, group: null, fullWidth: false, width: null }
    return <ChartExample />
  }
  const block = BLOCK_CHARTS[name]
  if (block) {
    window.__chart = { name, group: "blocks", fullWidth: false, width: block.width }
    const Comp = block.component
    return (
      <div data-chart-frame="block" style={{ width: `${block.width}px` }}>
        <Comp />
      </div>
    )
  }
  const extra = extraCharts[name]
  if (extra) {
    window.__chart = { name, group: extra.group, fullWidth: false, width: extra.width }
    const Comp = extra.component
    return (
      <div data-chart-frame="extra" style={{ width: `${extra.width}px` }}>
        <ComponentPreview>
          <Comp />
        </ComponentPreview>
      </div>
    )
  }
  const hit = index[name]
  if (!hit) return null
  const width = hit.item.fullWidth ? FULL_WIDTH : REGULAR_WIDTH
  window.__chart = { name, group: hit.group, fullWidth: !!hit.item.fullWidth, width }
  const Comp = hit.item.component
  return (
    <div data-chart-frame={hit.item.fullWidth ? "full" : "regular"} style={{ width: `${width}px` }}>
      <ComponentPreview>
        <Comp />
      </ComponentPreview>
    </div>
  )
}

function surfacesReady() {
  const containers = document.querySelectorAll("[data-slot=chart]")
  if (!containers.length) return false
  for (const c of Array.from(containers)) {
    const svg = c.querySelector("svg.recharts-surface")
    if (!svg || svg.getBoundingClientRect().width <= 0) return false
  }
  return true
}

const el = element()
if (!el) {
  window.__error = `unknown chart: ${name}`
} else {
  createRoot(root).render(el)
  const poll = () => {
    if (surfacesReady()) {
      requestAnimationFrame(() => requestAnimationFrame(() => (window.__ready = true)))
    } else {
      setTimeout(poll, 20)
    }
  }
  poll()
}
