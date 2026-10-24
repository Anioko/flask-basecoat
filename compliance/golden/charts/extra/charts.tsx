// Oracle charts for the forms shadcn has no original for (rulings R18 and R19). They are written like the
// upstream charts (shadcn Card + ChartContainer + Recharts 3.8 elements) and rendered by the same harness, so the
// library's port is compared with what Recharts itself draws for the same elements.
import { ChartBarWaterfall } from "./chart-bar-waterfall"
import { ChartMatrixTwoByTwo } from "./chart-matrix-two-by-two"
import { ChartScatterDefault } from "./chart-scatter-default"

export const EXTRA_WIDTH = 640

export const extraCharts: Record<string, { group: string; width: number; component: React.ComponentType }> = {
  "chart-scatter-default": { group: "scatter", width: 384, component: ChartScatterDefault },
  "chart-matrix-two-by-two": { group: "matrix", width: EXTRA_WIDTH, component: ChartMatrixTwoByTwo },
  "chart-bar-waterfall": { group: "bar", width: EXTRA_WIDTH, component: ChartBarWaterfall },
}
