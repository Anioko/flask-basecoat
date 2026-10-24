import * as React from "react"
import { Toast } from "@base-ui/react/toast"
import { Toaster } from "@/registry/bases/base/ui/toast"
import { Button } from "@/registry/bases/radix/ui/button"
import { Example, ExampleWrapper } from "@/registry/bases/radix/components/example"

export default function ToastScenario() {
  return (
    <ExampleWrapper>
      <Example title="Toaster">
        <Toast.Provider>
          <Button variant="outline">Show toast</Button>
          <Toaster />
        </Toast.Provider>
      </Example>
    </ExampleWrapper>
  )
}
