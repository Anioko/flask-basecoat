"use client"

import {
  CartesianGrid,
  LabelList,
  ReferenceArea,
  ReferenceLine,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts"

import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/registry/new-york-v4/ui/card"
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@/registry/new-york-v4/ui/toggle-group"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/registry/new-york-v4/ui/chart"

export const description = "A two-by-two matrix: value against cost"

const chartData = [
  { option: "SSO rollout", cost: 60, value: 82, effort: 6 },
  { option: "Retire legacy CRM", cost: 90, value: 68, effort: 10 },
  { option: "API gateway", cost: 120, value: 74, effort: 14 },
  { option: "Data lake", cost: 280, value: 88, effort: 40 },
  { option: "ERP upgrade", cost: 300, value: 76, effort: 52 },
  { option: "Mainframe exit", cost: 250, value: 62, effort: 36 },
  { option: "Wiki cleanup", cost: 30, value: 22, effort: 3 },
  { option: "Portal rename", cost: 70, value: 35, effort: 4 },
  { option: "Custom BI suite", cost: 280, value: 30, effort: 30 },
  { option: "On-prem refresh", cost: 220, value: 18, effort: 20 },
]

const chartConfig = {
  value: {
    label: "Value",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig

const label = (value: string) => ({
  value,
  position: "insideTopLeft" as const,
  offset: 8,
  fill: "var(--foreground)",
  fontSize: 12,
})

export function ChartMatrixTwoByTwo() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Matrix - Value against Cost</CardTitle>
        <CardDescription>Ten options, split at a cost of 200 and a value of 50</CardDescription>
        <CardAction>
          <ToggleGroup
            type="single"
            defaultValue="chart"
            variant="outline"
            size="sm"
            spacing={2}
            aria-label="View"
          >
            <ToggleGroupItem value="chart">Chart</ToggleGroupItem>
            <ToggleGroupItem value="table">Table</ToggleGroupItem>
          </ToggleGroup>
        </CardAction>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[544px] w-[560px]"
        >
          <ScatterChart
            accessibilityLayer
            margin={{ top: 16, right: 24, bottom: 8, left: 8 }}
          >
            <CartesianGrid />
            <ReferenceArea
              x1={0}
              x2={200}
              y1={94}
              y2={100}
              fill="var(--chart-2)"
              fillOpacity={0.1}
              stroke="none"
              label={label("Quick wins")}
            />
            <ReferenceArea
              x1={200}
              x2={400}
              y1={94}
              y2={100}
              fill="var(--chart-1)"
              fillOpacity={0.1}
              stroke="none"
              label={label("Major projects")}
            />
            <ReferenceArea
              x1={0}
              x2={200}
              y1={44}
              y2={50}
              fill="var(--chart-4)"
              fillOpacity={0.1}
              stroke="none"
              label={label("Fill-ins")}
            />
            <ReferenceArea
              x1={200}
              x2={400}
              y1={44}
              y2={50}
              fill="var(--chart-5)"
              fillOpacity={0.1}
              stroke="none"
              label={label("Reconsider")}
            />
            <XAxis
              type="number"
              dataKey="cost"
              name="Cost"
              domain={[0, 400]}
              ticks={[0, 100, 200, 300, 400]}
              height={56}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              label={{
                value: "Cost to deliver ($ thousands)",
                position: "insideBottom",
                offset: 0,
                fill: "var(--muted-foreground)",
              }}
            />
            <YAxis
              type="number"
              dataKey="value"
              name="Value"
              domain={[0, 100]}
              ticks={[0, 25, 50, 75, 100]}
              width={64}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              label={{
                value: "Value to the business (score)",
                angle: -90,
                position: "insideLeft",
                offset: 8,
                fill: "var(--muted-foreground)",
                style: { textAnchor: "middle" },
              }}
            />
            <ZAxis
              type="number"
              dataKey="effort"
              name="Effort (person-weeks)"
              range={[60, 400]}
            />
            <ReferenceLine
              x={200}
              stroke="var(--muted-foreground)"
              strokeDasharray="4 4"
            />
            <ReferenceLine
              y={50}
              stroke="var(--muted-foreground)"
              strokeDasharray="4 4"
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(_, payload) => payload?.[0]?.payload.option}
                />
              }
            />
            <Scatter data={chartData} fill="var(--color-value)">
              <LabelList
                dataKey="option"
                position="right"
                offset={8}
                className="fill-foreground"
                fontSize={12}
              />
            </Scatter>
          </ScatterChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-sm">
        <div className="leading-none text-muted-foreground">
          Bubble size shows effort in person-weeks
        </div>
      </CardFooter>
    </Card>
  )
}
