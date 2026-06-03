import { supabase } from "./supabase";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getAuthHeaders(): Promise<Record<string, string>> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) throw new Error("Not authenticated");
  return { Authorization: `Bearer ${session.access_token}` };
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const authHeaders = await getAuthHeaders();
  const isFormData = options.body instanceof FormData;
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...authHeaders,
      ...options.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  receipts: {
    upload: (formData: FormData) =>
      apiFetch<any>("/api/receipts/upload", { method: "POST", body: formData }),
    confirm: (receiptId: string, items: any[]) =>
      apiFetch<any>(`/api/receipts/${receiptId}/confirm`, {
        method: "POST",
        body: JSON.stringify({ items }),
      }),
    list: () => apiFetch<any[]>("/api/receipts/"),
    evalSummary: () => apiFetch<any>("/api/receipts/eval-summary"),
  },
  inventory: {
    list: () => apiFetch<any[]>("/api/inventory/"),
    expiring: () => apiFetch<any[]>("/api/inventory/expiring"),
    update: (id: string, payload: object) =>
      apiFetch<any>(`/api/inventory/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
    delete: (id: string) => apiFetch<any>(`/api/inventory/${id}`, { method: "DELETE" }),
    addManual: (payload: object) =>
      apiFetch<any>("/api/inventory/manual", { method: "POST", body: JSON.stringify(payload) }),
  },
  recipes: {
    suggest: () => apiFetch<any>("/api/recipes/suggest"),
    generate: () => apiFetch<any>("/api/recipes/generate"),
    eval: () => apiFetch<any>("/api/recipes/eval"),
  },
  shopping: {
    generate: (recipeId: string) =>
      apiFetch<any>("/api/shopping/generate", {
        method: "POST",
        body: JSON.stringify({ recipe_id: recipeId }),
      }),
    create: (title: string, items: { name: string; quantity?: number | null; unit?: string | null }[]) =>
      apiFetch<any>("/api/shopping/create", {
        method: "POST",
        body: JSON.stringify({ title, items }),
      }),
    list: () => apiFetch<any[]>("/api/shopping/"),
    toggleItem: (listId: string, itemName: string) =>
      apiFetch<any>(`/api/shopping/${listId}/item`, {
        method: "PATCH",
        body: JSON.stringify({ item_name: itemName }),
      }),
  },
  notifications: {
    subscribe: (sub: object) =>
      apiFetch<any>("/api/notifications/subscribe", {
        method: "POST",
        body: JSON.stringify(sub),
      }),
  },
};
