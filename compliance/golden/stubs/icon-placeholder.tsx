// Golden-oracle stand-in for the docs site's IconPlaceholder.
// The upstream site renders the Lucide icon by default; this stub does exactly that
// without the search-param plumbing, so the rendered SVG matches the live site.
import * as React from "react"
import * as lucide from "lucide-react"

export function IconPlaceholder({ lucide: name, tabler, hugeicons, phosphor, remixicon, ...props }: any) {
  const key = name && (lucide as any)[name + "Icon"] ? name + "Icon" : name
  const Comp = (key && (lucide as any)[key]) || lucide.SquareIcon
  return <Comp {...props} />
}
