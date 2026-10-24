// Bundles charts/entry.tsx for the browser golden: esbuild, IIFE, production React, tsconfig path aliases.
// Usage (from compliance/golden): node charts/build.mjs   or   npm run charts:bundle
import * as path from "node:path"
import { fileURLToPath } from "node:url"
import { build } from "esbuild"

const here = path.dirname(fileURLToPath(import.meta.url))

await build({
  entryPoints: [path.join(here, "entry.tsx")],
  outfile: path.join(here, "bundle.js"),
  bundle: true,
  format: "iife",
  platform: "browser",
  target: "es2022",
  jsx: "automatic",
  tsconfig: path.resolve(here, "../tsconfig.json"),
  define: { "process.env.NODE_ENV": '"production"' },
  minify: true,
  legalComments: "none",
  logLevel: "warning",
})
console.log("charts/bundle.js written")
