"use client"

import { CartesianGrid, Scatter, ScatterChart, XAxis, YAxis } from "recharts"

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
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/registry/new-york-v4/ui/chart"

export const description = "A scatter chart"

const chartData = [
  { cost: 60, value: 82 },
  { cost: 90, value: 68 },
  { cost: 150, value: 74 },
  { cost: 280, value: 88 },
  { cost: 300, value: 76 },
  { cost: 250, value: 62 },
  { cost: 30, value: 22 },
  { cost: 70, value: 35 },
  { cost: 280, value: 30 },
  { cost: 220, value: 18 },
]

const chartConfig = {
  value: {
    label: "Value",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig

export function ChartScatterDefault() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Scatter Chart</CardTitle>
        <CardDescription>Delivery cost against value, ten options</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig}>
          <ScatterChart accessibilityLayer margin={{ left: 12, right: 12 }}>
            <CartesianGrid />
            <XAxis
              type="number"
              dataKey="cost"
              name="Cost"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <YAxis
              type="number"
              dataKey="value"
              name="Value"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            <Scatter data={chartData} fill="var(--color-value)" />
          </ScatterChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-sm">
        <div className="leading-none text-muted-foreground">
          Cost in thousands of dollars, value as a score out of 100
        </div>
      </CardFooter>
    </Card>
  )
}
