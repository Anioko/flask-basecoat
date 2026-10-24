import * as React from "react"
import { DirectionProvider } from "@/registry/bases/radix/ui/direction"
import { Button } from "@/registry/bases/radix/ui/button"
import { Example, ExampleWrapper } from "@/registry/bases/radix/components/example"

export default function DirectionScenario() {
  return (
    <ExampleWrapper>
      <Example title="Right to left">
        <DirectionProvider dir="rtl">
          <div dir="rtl" data-slot="direction" className="flex gap-2">
            <Button>الأول</Button>
            <Button variant="outline">الثاني</Button>
          </div>
        </DirectionProvider>
      </Example>
    </ExampleWrapper>
  )
}
