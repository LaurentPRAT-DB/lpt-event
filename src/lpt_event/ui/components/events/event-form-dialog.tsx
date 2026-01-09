import { useState, useEffect } from "react";
import { Loader2, Plus, Pencil } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  EventRead,
  EventCreate,
  useCreateEvent,
  useUpdateEvent,
} from "@/lib/api";
import { toast } from "sonner";

const DAYS_OF_WEEK = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

interface EventFormDialogProps {
  event?: EventRead;
  trigger?: React.ReactNode;
}

export function EventFormDialog({ event, trigger }: EventFormDialogProps) {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<EventCreate>>({
    title: "",
    short_description: "",
    detailed_description: "",
    city: "",
    days_of_week: [],
    cost_usd: 0,
    picture_url: "",
  });

  const createMutation = useCreateEvent();
  const updateMutation = useUpdateEvent();

  const isEditing = !!event;
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  // Populate form data when editing
  useEffect(() => {
    if (event && open) {
      setFormData({
        title: event.title,
        short_description: event.short_description,
        detailed_description: event.detailed_description,
        city: event.city,
        days_of_week: event.days_of_week,
        cost_usd: event.cost_usd,
        picture_url: event.picture_url,
      });
    } else if (!open) {
      // Reset form when dialog closes
      setFormData({
        title: "",
        short_description: "",
        detailed_description: "",
        city: "",
        days_of_week: [],
        cost_usd: 0,
        picture_url: "",
      });
    }
  }, [event, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (isEditing) {
        await updateMutation.mutateAsync({
          eventId: event.id,
          data: formData,
        });
        toast.success("Event updated successfully!");
      } else {
        await createMutation.mutateAsync({ data: formData as EventCreate });
        toast.success("Event created successfully!");
      }
      setOpen(false);
    } catch (error) {
      toast.error(
        isEditing
          ? "Failed to update event. Please try again."
          : "Failed to create event. Please try again."
      );
    }
  };

  const toggleDay = (day: string) => {
    setFormData((prev) => {
      const days = prev.days_of_week || [];
      if (days.includes(day)) {
        return { ...prev, days_of_week: days.filter((d) => d !== day) };
      } else {
        return { ...prev, days_of_week: [...days, day] };
      }
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            {isEditing ? (
              <>
                <Pencil className="h-4 w-4 mr-2" />
                Edit Event
              </>
            ) : (
              <>
                <Plus className="h-4 w-4 mr-2" />
                Create Event
              </>
            )}
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit Event" : "Create New Event"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update the event details below."
              : "Fill in the details to create a new event."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              required
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              placeholder="Event title"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="short_description">Short Description *</Label>
            <Input
              id="short_description"
              required
              value={formData.short_description}
              onChange={(e) =>
                setFormData({ ...formData, short_description: e.target.value })
              }
              placeholder="Brief description"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="detailed_description">
              Detailed Description *
            </Label>
            <Textarea
              id="detailed_description"
              required
              value={formData.detailed_description}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  detailed_description: e.target.value,
                })
              }
              placeholder="Full event description"
              rows={4}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="city">City *</Label>
              <Input
                id="city"
                required
                value={formData.city}
                onChange={(e) =>
                  setFormData({ ...formData, city: e.target.value })
                }
                placeholder="Event city"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cost_usd">Cost (USD) *</Label>
              <Input
                id="cost_usd"
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.cost_usd}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    cost_usd: parseFloat(e.target.value),
                  })
                }
                placeholder="0.00"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="picture_url">Picture URL *</Label>
            <Input
              id="picture_url"
              type="url"
              required
              value={formData.picture_url}
              onChange={(e) =>
                setFormData({ ...formData, picture_url: e.target.value })
              }
              placeholder="https://example.com/image.jpg"
            />
          </div>

          <div className="space-y-2">
            <Label>Days of Week *</Label>
            <div className="flex flex-wrap gap-2">
              {DAYS_OF_WEEK.map((day) => (
                <Badge
                  key={day}
                  variant={
                    formData.days_of_week?.includes(day)
                      ? "default"
                      : "outline"
                  }
                  className="cursor-pointer"
                  onClick={() => toggleDay(day)}
                >
                  {day}
                </Badge>
              ))}
            </div>
            {formData.days_of_week && formData.days_of_week.length === 0 && (
              <p className="text-xs text-muted-foreground">
                Select at least one day
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEditing ? "Update Event" : "Create Event"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
