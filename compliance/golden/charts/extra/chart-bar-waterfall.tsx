"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts"

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/registry/new-york-v4/ui/card"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/registry/new-york-v4/ui/chart"

export const description = "A cost bridge: a stacked bar with a transparent base"

const chartData = [
  { step: "Current cost", base: 0, fall: null, rise: null, total: 4800, label: "$4,800k" },
  { step: "Licences", base: 3900, fall: 900, rise: null, total: null, label: "-$900k" },
  { step: "Hosting", base: 3200, fall: 700, rise: null, total: null, label: "-$700k" },
  { step: "Support", base: 2700, fall: 500, rise: null, total: null, label: "-$500k" },
  { step: "Migration", base: 2700, fall: null, rise: 650, total: null, label: "+$650k" },
  { step: "Three-year total", base: 0, fall: null, rise: null, total: 3350, label: "$3,350k" },
]

const chartConfig = {
  base: {
    label: "Base",
  },
  fall: {
    label: "Decrease",
    color: "var(--chart-5)",
  },
  rise: {
    label: "Increase",
    color: "var(--chart-2)",
  },
  total: {
    label: "Total",
    color: "var(--primary)",
  },
} satisfies ChartConfig

export function ChartBarWaterfall() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Bar Chart - Waterfall</CardTitle>
        <CardDescription>Three-year cost of the current estate to the target, $ thousands</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="min-w-[560px]">
          <BarChart accessibilityLayer data={chartData}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="step"
              tickLine={false}
              tickMargin={10}
              axisLine={false}
              interval={0}
            />
            <YAxis tickLine={false} axisLine={false} tickMargin={8} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            <ReferenceLine
              segment={[{ x: "Current cost", y: 4800 }, { x: "Licences", y: 4800 }]}
              stroke="var(--muted-foreground)"
              strokeDasharray="3 3"
            />
            <ReferenceLine
              segment={[{ x: "Licences", y: 3900 }, { x: "Hosting", y: 3900 }]}
              stroke="var(--muted-foreground)"
              strokeDasharray="3 3"
            />
            <ReferenceLine
              segment={[{ x: "Hosting", y: 3200 }, { x: "Support", y: 3200 }]}
              stroke="var(--muted-foreground)"
              strokeDasharray="3 3"
            />
            <ReferenceLine
              segment={[{ x: "Support", y: 2700 }, { x: "Migration", y: 2700 }]}
              stroke="var(--muted-foreground)"
              strokeDasharray="3 3"
            />
            <ReferenceLine
              segment={[{ x: "Migration", y: 3350 }, { x: "Three-year total", y: 3350 }]}
              stroke="var(--muted-foreground)"
              strokeDasharray="3 3"
            />
            <Bar dataKey="base" stackId="a" fill="transparent" legendType="none" tooltipType="none" />
            <Bar dataKey="fall" stackId="a" fill="var(--color-fall)" stroke="var(--muted-foreground)" strokeWidth={1}>
              <LabelList dataKey="label" position="top" offset={8} className="fill-foreground" fontSize={12} />
            </Bar>
            <Bar dataKey="rise" stackId="a" fill="var(--color-rise)" stroke="var(--muted-foreground)" strokeWidth={1}>
              <LabelList dataKey="label" position="top" offset={8} className="fill-foreground" fontSize={12} />
            </Bar>
            <Bar dataKey="total" stackId="a" fill="var(--color-total)" stroke="var(--muted-foreground)" strokeWidth={1}>
              <LabelList dataKey="label" position="top" offset={8} className="fill-foreground" fontSize={12} />
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-sm">
        <div className="leading-none text-muted-foreground">
          Starts at 4,800, falls by 2,100, rises by 650 and ends at 3,350
        </div>
      </CardFooter>
    </Card>
  )
}
