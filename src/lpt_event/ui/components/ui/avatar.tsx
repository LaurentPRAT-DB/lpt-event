import * as React from "react";

import { cn } from "@/lib/utils";

function Avatar({
  className,
  ...props
}: React.ImgHTMLAttributes<HTMLImageElement> & { children?: React.ReactNode }) {
  const { children, ...imgProps } = props as any;
  return (
    <div
      data-slot="avatar"
      className={cn(
        "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full border border-border bg-muted",
        className,
      )}
    >
      {imgProps.src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          alt={imgProps.alt}
          className="h-full w-full object-cover"
          {...imgProps}
        />
      ) : (
        children
      )}
    </div>
  );
}

function AvatarFallback({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="avatar-fallback"
      className={cn(
        "flex h-full w-full items-center justify-center bg-muted text-xs font-medium text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}

export { Avatar, AvatarFallback };


