"use client";

import { type Icon } from "@tabler/icons-react";

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem
} from "@/components/ui/sidebar";
import data from "@/app/(site)/[slug]/data.json";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";

export function NavMain({
  items
}: {
  items: {
    title: string;
    url: string;
    icon?: Icon;
  }[];
}) {
  const pathname = usePathname();

  return (
    <SidebarGroup>
      <SidebarGroupLabel className="opacity-60">Examples</SidebarGroupLabel>
      <SidebarGroupContent className="flex flex-col gap-2">
        <SidebarMenu>
          {data.map((item, i) => (
            <SidebarMenuItem key={item.meta.title}>
              <SidebarMenuButton
                asChild
                tooltip={item.meta.title}
                isActive={pathname.replace("/", "") === item.href}
                className="data-[active=true]:bg-primary data-[active=true]:text-primary-foreground">
                <Link href={item.href} className={cn({ "opacity-45": item.isComing })}>
                  <span>{item.meta.title}</span>
                  {item?.isComing ? (
                    <SidebarMenuBadge className="opacity-45">Soon</SidebarMenuBadge>
                  ) : (
                    false
                  )}
                  {item?.isNew ? (
                    <SidebarMenuBadge className="text-green-600">New</SidebarMenuBadge>
                  ) : (
                    false
                  )}
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
