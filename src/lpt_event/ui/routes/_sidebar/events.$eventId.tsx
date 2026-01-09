import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, CalendarDays, MapPin, DollarSign } from "lucide-react";

import { useGetEvent } from "@/lib/api";
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

export const Route = createFileRoute("/_sidebar/events/$eventId")({
  component: () => <EventDetail />,
});

function EventDetailSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-6 w-32" />
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

function EventDetail() {
  const { eventId } = Route.useParams();
  const { data, isLoading, isError } = useGetEvent(parseInt(eventId));

  if (isLoading) {
    return <EventDetailSkeleton />;
  }

  if (isError || !data) {
    return (
      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">Event not found</CardTitle>
          <CardDescription>
            We couldn't find this event. It may have been removed or the link is
            invalid.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild variant="outline">
            <Link to="/events">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to events
            </Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const event = data.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button asChild variant="ghost" size="sm" className="-ml-2">
          <Link to="/events">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to events
          </Link>
        </Button>
      </div>

      <Card className="border-primary/20">
        <CardHeader className="space-y-4">
          <div className="overflow-hidden rounded-lg border bg-muted/40">
            {/* eslint-disable-next-line jsx-a11y/alt-text, @next/next/no-img-element */}
            <img
              src={event.picture_url}
              className="max-h-72 w-full object-cover"
            />
          </div>
          <div className="space-y-2">
            <CardTitle className="text-2xl">{event.title}</CardTitle>
            <CardDescription>{event.short_description}</CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {event.city}
            </span>
            <span className="inline-flex items-center gap-1">
              <CalendarDays className="h-4 w-4" />
              {event.days_of_week.join(", ")}
            </span>
            <span className="inline-flex items-center gap-1">
              <DollarSign className="h-4 w-4" />
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
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold">About this event</h2>
            <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-line">
              {event.detailed_description}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


