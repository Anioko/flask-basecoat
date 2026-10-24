/**
 * Golden oracle renderer.
 * Renders every pinned upstream example (apps/v4/registry/bases/radix/examples) with
 * ReactDOMServer.renderToStaticMarkup and writes one HTML document per component to out/.
 * The output is the upstream DOM, byte for byte what React would hydrate, so computed styles
 * taken from it in a browser are the definition of "looks like shadcn".
 */
import * as fs from "node:fs"
import * as path from "node:path"
import { pathToFileURL, fileURLToPath } from "node:url"
import * as React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { TooltipProvider } from "../upstream/shadcn/radix/ui/tooltip"

const here = path.dirname(fileURLToPath(import.meta.url))
const examplesDir = path.resolve(here, "../upstream/shadcn/radix/examples")
const outDir = path.resolve(here, "out")
const registry = JSON.parse(fs.readFileSync(path.resolve(here, "../upstream/shadcn/registry/index.json"), "utf8"))
const names: string[] = registry.filter((i: any) => i.type === "registry:ui").map((i: any) => i.name)
const only = process.argv.slice(2)

fs.mkdirSync(outDir, { recursive: true })
const manifest: Record<string, any> = {}

function wrap(name: string, body: string) {
  return `<!doctype html>
<html lang="en" class="style-vega">
<head>
<meta charset="utf-8">
<title>golden: ${name}</title>
<link rel="stylesheet" href="golden.css">
</head>
<body data-golden="${name}">
${body}
</body>
</html>
`
}

for (const name of names) {
  if (only.length && !only.includes(name)) continue
  let file = path.join(examplesDir, `${name}-example.tsx`)
  let source = "upstream-example"
  if (!fs.existsSync(file)) {
    file = path.resolve(here, "scenarios", `${name}.tsx`)
    source = "custom-scenario"
    if (!fs.existsSync(file)) {
      manifest[name] = { status: "no-upstream-example" }
      continue
    }
  }
  try {
    const mod = await import(pathToFileURL(file).href)
    const Comp = mod.default
    const html = renderToStaticMarkup(React.createElement(TooltipProvider, null, React.createElement(Comp)))
    fs.writeFileSync(path.join(outDir, `${name}.html`), wrap(name, html))
    const slots = Array.from(html.matchAll(/data-slot="([^"]+)"/g)).map((m) => m[1])
    manifest[name] = { status: "rendered", source, bytes: html.length, slots: Array.from(new Set(slots)).sort() }
  } catch (err: any) {
    manifest[name] = { status: "render-error", error: String(err?.message || err).split("\n")[0] }
  }
}

// Blocks: every public block in the pinned radix registry (page.tsx is the block's root).
const blocksDir = path.resolve(here, "../upstream/shadcn/radix/blocks")
const blockNames = fs.readdirSync(blocksDir).filter((n) => /^(dashboard|login|signup|sidebar)-\d+$/.test(n)).sort()
fs.mkdirSync(path.join(outDir, "blocks"), { recursive: true })
for (const name of blockNames) {
  if (only.length && !only.includes(name)) continue
  const file = path.join(blocksDir, name, "page.tsx")
  try {
    const mod = await import(pathToFileURL(file).href)
    const html = renderToStaticMarkup(React.createElement(TooltipProvider, null, React.createElement(mod.default)))
    fs.writeFileSync(path.join(outDir, "blocks", `${name}.html`), wrap(name, html).replace('href="golden.css"', 'href="../golden.css"'))
    const slots = Array.from(html.matchAll(/data-slot="([^"]+)"/g)).map((m) => m[1])
    manifest[`block:${name}`] = { status: "rendered", source: "upstream-block", bytes: html.length, slots: Array.from(new Set(slots)).sort() }
  } catch (err: any) {
    manifest[`block:${name}`] = { status: "render-error", error: String(err?.message || err).split(String.fromCharCode(10))[0] }
  }
}

fs.writeFileSync(path.join(outDir, "manifest.json"), JSON.stringify(manifest, null, 2))
const counts = Object.values(manifest).reduce((a: any, m: any) => ((a[m.status] = (a[m.status] || 0) + 1), a), {})
console.log(JSON.stringify(counts))
for (const [n, m] of Object.entries(manifest)) if (m.status !== "rendered") console.log(n, m.status, m.error || "")
