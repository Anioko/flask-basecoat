import * as React from "react"
import { useForm } from "react-hook-form"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/registry/new-york-v4/ui/form"
import { Input } from "@/registry/bases/radix/ui/input"
import { Button } from "@/registry/bases/radix/ui/button"
import { Example, ExampleWrapper } from "@/registry/bases/radix/components/example"

function Demo({ withError }: { withError?: boolean }) {
  const form = useForm({ defaultValues: { username: "" } })
  if (withError) {
    form.setError("username", { type: "manual", message: "Username must be at least 2 characters." })
  }
  return (
    <Form {...form}>
      <form className="space-y-8 w-full">
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="shadcn" {...field} />
              </FormControl>
              <FormDescription>This is your public display name.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  )
}

export default function FormScenario() {
  return (
    <ExampleWrapper>
      <Example title="Default"><Demo /></Example>
      <Example title="With error"><Demo withError /></Example>
    </ExampleWrapper>
  )
}
