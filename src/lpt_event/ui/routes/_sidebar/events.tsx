import { createFileRoute, Link } from "@tanstack/react-router";
import { CalendarDays, MapPin, DollarSign, ChevronRight, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";

import { useEventsQuery, useDeleteEventMutation } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EventFormDialog } from "@/components/events/event-form-dialog";
import { toast } from "sonner";

export const Route = createFileRoute("/_sidebar/events")({
  component: () => <EventsPage />,
});

function EventsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i} className="border-primary/10">
          <CardHeader>
            <Skeleton className="h-40 w-full rounded-lg mb-4" />
            <Skeleton className="h-5 w-32 mb-2" />
            <Skeleton className="h-4 w-48" />
          </CardHeader>
          <CardContent className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-36" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function EventsPage() {
  const { data, isLoading, isError, refetch } = useEventsQuery();
  const deleteMutation = useDeleteEventMutation();
  const [deletingId, setDeletingId] = useState<number | null>(null);

  if (isLoading) {
    return <EventsSkeleton />;
  }

  if (isError || !data) {
    return (
      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            Failed to load events
          </CardTitle>
          <CardDescription>
            Make sure the backend is running and reachable, then try again.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) {
      return;
    }

    setDeletingId(id);
    try {
      await deleteMutation.mutateAsync(id);
      toast.success("Event deleted successfully!");
    } catch (error) {
      toast.error("Failed to delete event. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <CalendarDays className="h-5 w-5" />
            Events
          </h1>
          <p className="text-sm text-muted-foreground">
            Browse, create, edit, and manage your events.
          </p>
        </div>
        <EventFormDialog />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.map((event) => (
          <Card
            key={event.id}
            className="group border-primary/10 hover:border-primary/40 transition-colors"
          >
            <CardHeader className="space-y-3">
              <div className="overflow-hidden rounded-lg border bg-muted/40">
                {/* eslint-disable-next-line jsx-a11y/alt-text, @next/next/no-img-element */}
                <img
                  src={event.picture_url}
                  className="h-40 w-full object-cover transition-transform group-hover:scale-[1.02]"
                />
              </div>
              <CardTitle className="line-clamp-1">{event.title}</CardTitle>
              <CardDescription className="line-clamp-2">
                {event.short_description}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {event.city}
                </span>
                <span className="inline-flex items-center gap-1">
                  <DollarSign className="h-3 w-3" />
                  {event.cost_usd === 0 ? "Free" : `$${event.cost_usd.toFixed(2)}`}
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                {event.days_of_week.map((day) => (
                  <Badge key={day} variant="secondary">
                    {day}
                  </Badge>
                ))}
              </div>
              <div className="pt-2 space-y-2">
                <Button
                  variant="outline"
                  size="sm"
                  asChild
                  className="w-full justify-between"
                >
                  <Link to="/events/$eventId" params={{ eventId: event.id }}>
                    View details
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                </Button>
                <div className="flex gap-2">
                  <EventFormDialog
                    event={event}
                    trigger={
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                      >
                        <Pencil className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                    }
                  />
                  <Button
                    variant="destructive"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleDelete(event.id, event.title)}
                    disabled={deletingId === event.id}
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    Delete
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}


