import {
  useQuery,
  useSuspenseQuery,
  useMutation,
  useQueryClient,
  QueryKey,
} from "@tanstack/react-query";

const API_BASE = "/api";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request to ${path} failed with ${res.status}`);
  }

  return (await res.json()) as T;
}

// --- User API (existing profile & sidebar footer) ---

export function useCurrentUserSuspense(selector?: any) {
  const select = selector?.query?.select;

  return useSuspenseQuery({
    queryKey: ["currentUser"] as QueryKey,
    // Wrap in { data: ... } to match the selector() shape used by profile/sidebar
    queryFn: async () => ({ data: await fetchJSON<any>("/current-user") }),
    select,
  });
}

// --- Events API ---

export type Event = {
  id: number;
  title: string;
  short_description: string;
  detailed_description: string;
  city: string;
  days_of_week: string[];
  cost_usd: number;
  picture_url: string;
};

export type EventCreate = Omit<Event, "id">;
export type EventUpdate = Partial<EventCreate>;

export function useEventsQuery() {
  return useQuery<Event[]>({
    queryKey: ["events"],
    queryFn: () => fetchJSON<Event[]>("/events"),
  });
}

export function useEventQuery(eventId: number | string | undefined) {
  return useQuery<Event>({
    enabled: !!eventId,
    queryKey: ["events", eventId],
    queryFn: () => fetchJSON<Event>(`/events/${eventId}`),
  });
}

export function useCreateEventMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: EventCreate) =>
      fetchJSON<Event>("/events", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

export function useUpdateEventMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: EventUpdate }) =>
      fetchJSON<Event>(`/events/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["events", variables.id] });
    },
  });
}

export function useDeleteEventMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) =>
      fetchJSON<{ ok: boolean; message: string }>(`/events/${id}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });
}


