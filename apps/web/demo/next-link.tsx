import type { AnchorHTMLAttributes, ReactNode } from "react";
import { routeOf } from "./router";

type Props = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & { href: string; children?: ReactNode };

/** Hash-routed stand-in for next/link, so the demo works from a single published page. */
export default function Link({ href, children, ...rest }: Props) {
  return <a href={`#${routeOf(href)}`} {...rest}>{children}</a>;
}
