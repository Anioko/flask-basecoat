// The docs site reads the active style and icon library from the URL; the oracle pins both.
export function useDesignSystemSearchParams() {
  return [{ style: "vega", iconLibrary: "lucide", base: "radix", theme: "neutral" }, () => {}] as const
}
