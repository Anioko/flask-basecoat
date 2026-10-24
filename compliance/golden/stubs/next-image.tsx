import * as React from "react"
export default function Image({ src, alt, width, height, fill, priority, quality, placeholder, blurDataURL, loader, unoptimized, ...props }: any) {
  return <img src={typeof src === "string" ? src : src?.src} alt={alt} width={width} height={height} {...props} />
}
