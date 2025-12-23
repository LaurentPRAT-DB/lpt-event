import * as React from "react";
import { createContext, useContext, useState } from "react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type SidebarContextValue = {
  collapsed: boolean;
  toggle: () => void;
};

const SidebarContext = createContext<SidebarContextValue | null>(null);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const toggle = () => setCollapsed((c) => !c);

  return (
    <SidebarContext.Provider value={{ collapsed, toggle }}>
      <div className="flex h-screen w-full bg-background text-foreground">
        {children}
      </div>
    </SidebarContext.Provider>
  );
}

function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) {
    throw new Error("Sidebar components must be used within <SidebarProvider>");
  }
  return ctx;
}

export function Sidebar({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  const { collapsed } = useSidebar();
  return (
    <aside
      data-slot="sidebar"
      className={cn(
        "flex h-full flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-200",
        collapsed ? "w-16" : "w-64",
        className,
      )}
      {...props}
    />
  );
}

export function SidebarHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="sidebar-header"
      className={cn("border-b px-2 py-3", className)}
      {...props}
    />
  );
}

export function SidebarContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="sidebar-content"
      className={cn("flex-1 overflow-auto px-2 py-2", className)}
      {...props}
    />
  );
}

export function SidebarFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="sidebar-footer"
      className={cn("border-t px-2 py-2", className)}
      {...props}
    />
  );
}

export function SidebarInset({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <main
      data-slot="sidebar-inset"
      className={cn("flex-1 overflow-hidden bg-background", className)}
      {...props}
    />
  );
}

export function SidebarTrigger({
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { toggle, collapsed } = useSidebar();
  return (
    <Button
      type="button"
      variant="outline"
      size="icon-sm"
      data-slot="sidebar-trigger"
      className={cn("shrink-0", className)}
      onClick={(e) => {
        toggle();
        props.onClick?.(e);
      }}
    >
      <span className="sr-only">Toggle sidebar</span>
      <div
        className={cn(
          "flex flex-col gap-0.5 transition-transform",
          collapsed && "translate-x-[1px]",
        )}
      >
        <span className="h-0.5 w-3 rounded-full bg-foreground" />
        <span className="h-0.5 w-3 rounded-full bg-foreground" />
        <span className="h-0.5 w-3 rounded-full bg-foreground" />
      </div>
    </Button>
  );
}

export function SidebarRail({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  // Decorative rail to match shadcn's sidebar; kept minimal here.
  return (
    <div
      data-slot="sidebar-rail"
      className={cn("hidden lg:block", className)}
      {...props}
    />
  );
}

export function SidebarGroup({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="sidebar-group"
      className={cn("space-y-1", className)}
      {...props}
    />
  );
}

export function SidebarGroupContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="sidebar-group-content"
      className={cn("space-y-1", className)}
      {...props}
    />
  );
}

export function SidebarMenu({
  className,
  ...props
}: React.HTMLAttributes<HTMLUListElement>) {
  return (
    <ul
      data-slot="sidebar-menu"
      className={cn("space-y-1", className)}
      {...props}
    />
  );
}

export function SidebarMenuItem({
  className,
  ...props
}: React.LiHTMLAttributes<HTMLLIElement>) {
  return (
    <li
      data-slot="sidebar-menu-item"
      className={cn("", className)}
      {...props}
    />
  );
}

export interface SidebarMenuButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: "sm" | "md" | "lg";
}

export function SidebarMenuButton({
  className,
  size = "md",
  ...props
}: SidebarMenuButtonProps) {
  const sizes: Record<NonNullable<SidebarMenuButtonProps["size"]>, string> = {
    sm: "h-8 px-2 text-xs",
    md: "h-9 px-3 text-sm",
    lg: "h-10 px-3 text-sm",
  };

  return (
    <button
      type="button"
      data-slot="sidebar-menu-button"
      className={cn(
        "flex w-full items-center gap-2 rounded-lg border border-transparent bg-transparent px-3 text-left text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
        sizes[size],
        className,
      )}
      {...props}
    />
  );
}


