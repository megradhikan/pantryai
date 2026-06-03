"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import type { InventoryItem } from "@/lib/types";
import Nav from "@/components/Nav";
import StatusBadge from "@/components/StatusBadge";

const CAT_EMOJI: Record<string, string> = {
  Dairy: "🥛", Protein: "🥩", Produce: "🥬", Grains: "🌾",
  Snacks: "🍿", Beverages: "🧃", Frozen: "🧊", Condiments: "🫙", Other: "📦",
};
const CATEGORIES = ["Dairy", "Protein", "Produce", "Grains", "Snacks", "Beverages", "Frozen", "Condiments", "Other"];
type Filter = "all" | "expiring_soon" | "low" | "finished";

function fmtDate(s: string) {
  return new Date(s + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("all");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", category: "Produce", quantity: "1", unit: "" });
  const [newItemId, setNewItemId] = useState<string | null>(null);
  const [finishingId, setFinishingId] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_ev, session) => {
      if (!session) router.push("/");
      else load();
    });
    return () => subscription.unsubscribe();
  }, []);

  async function load() {
    try { setItems(await api.inventory.list()); }
    catch { router.push("/"); }
    finally { setLoading(false); }
  }

  async function decrement(item: InventoryItem) {
    if (item.quantity <= 0) return;
    const u = await api.inventory.update(item.id, { quantity: item.quantity - 1 });
    setItems((p) => p.map((i) => (i.id === item.id ? u : i)));
  }

  async function finish(item: InventoryItem) {
    setFinishingId(item.id);
    await new Promise((r) => setTimeout(r, 180));
    const u = await api.inventory.update(item.id, { is_finished: true });
    setItems((p) => p.map((i) => (i.id === item.id ? u : i)));
    setFinishingId(null);
  }

  async function remove(id: string) {
    await api.inventory.delete(id);
    setItems((p) => p.filter((i) => i.id !== id));
  }

  async function addItem(e: React.FormEvent) {
    e.preventDefault();
    const item = await api.inventory.addManual({
      name: form.name, category: form.category,
      quantity: parseFloat(form.quantity), unit: form.unit || undefined,
    });
    setItems((p) => [...p, item]);
    setNewItemId(item.id);
    setTimeout(() => setNewItemId(null), 600);
    setShowAdd(false);
    setForm({ name: "", category: "Produce", quantity: "1", unit: "" });
  }

  const filtered = items.filter((i) => {
    if (filter !== "all" && i.status !== filter) return false;
    return true;
  });

  const expiring = items.filter((i) => i.status === "expiring_soon" || i.status === "expired").length;

  return (
    <>
      <div className="page">
        <div className="page-header">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title">My Pantry</h1>
              <p className="page-subtitle">
                {greeting()} · {items.length} items
                {expiring > 0 && (
                  <span style={{ color: "var(--status-expiring)", fontWeight: 600 }}>
                    {" · "}{expiring} expiring
                  </span>
                )}
              </p>
            </div>
            <button
              onClick={() => { supabase.auth.signOut(); router.push("/"); }}
              className="text-xs font-medium"
              style={{ color: "var(--faint)" }}
            >
              Sign out
            </button>
          </div>
        </div>

        <div className="page-body">
          {/* Filters */}
          <div className="flex gap-2 mb-4 overflow-x-auto pb-1 no-scrollbar">
            {([["all", "All"], ["expiring_soon", "Expiring"], ["low", "Low"], ["finished", "Done"]] as const).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className="shrink-0 px-4 py-2 text-xs font-semibold transition-all"
                style={{
                  borderRadius: "var(--radius-full)",
                  background: filter === key ? "var(--primary)" : "var(--surface-raised)",
                  color: filter === key ? "white" : "var(--muted)",
                  boxShadow: filter === key ? "none" : "var(--shadow-sm)",
                }}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Add button */}
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="w-full py-3 text-sm font-medium mb-4 transition-colors"
            style={{
              borderRadius: "var(--radius-lg)",
              border: "1px dashed var(--faint)",
              color: "var(--muted)",
              background: "transparent",
            }}
          >
            + Add item
          </button>

          {showAdd && (
            <form onSubmit={addItem} className="card mb-4 space-y-3">
              <input required placeholder="Item name" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="input-field" />
              <div className="flex gap-2">
                <select value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="input-field flex-1">
                  {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                </select>
                <input type="number" min="0" step="0.1" required placeholder="Qty" value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                  className="input-field w-20" />
              </div>
              <input placeholder="Unit (optional)" value={form.unit}
                onChange={(e) => setForm({ ...form, unit: e.target.value })}
                className="input-field" />
              <div className="flex gap-2">
                <button type="submit" className="btn-primary flex-1">Add to pantry</button>
                <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary">Cancel</button>
              </div>
            </form>
          )}

          {/* Items */}
          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="card flex items-center gap-3" style={{ animationDelay: `${i * 60}ms` }}>
                  <div className="skeleton shrink-0" style={{ width: 40, height: 40, borderRadius: "50%" }} />
                  <div className="flex-1 space-y-2">
                    <div className="skeleton" style={{ height: 14, width: "65%" }} />
                    <div className="skeleton" style={{ height: 11, width: "45%" }} />
                  </div>
                  <div className="skeleton shrink-0" style={{ width: 72, height: 28, borderRadius: "var(--radius-full)" }} />
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-4xl mb-3" style={{ opacity: 0.5 }}>
                {items.length === 0 ? "🛍️" : "🔍"}
              </div>
              <p className="text-sm" style={{ color: "var(--muted)" }}>
                {items.length === 0
                  ? "Scan your first receipt to fill your pantry."
                  : "Nothing matches this filter."}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.map((item) => (
                <div
                  key={item.id}
                  className={`card flex items-center gap-3${newItemId === item.id ? " item-enter" : ""}`}
                  style={{
                    background:
                      item.status === "expired"      ? "oklch(0.97 0.02 25)"  :
                      item.status === "expiring_soon" ? "oklch(0.975 0.025 55)" :
                      "var(--surface-raised)",
                    opacity:    finishingId === item.id ? 0.35 : 1,
                    transform:  finishingId === item.id ? "scale(0.97)" : "scale(1)",
                    transition: "opacity 180ms ease-out, transform 180ms ease-out",
                  }}
                >
                  <span className="text-2xl shrink-0">{CAT_EMOJI[item.category] ?? "📦"}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm truncate" style={{ color: "var(--ink)" }}>{item.name}</p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                      {item.quantity}{item.unit ? ` ${item.unit}` : ""} · Exp {fmtDate(item.estimated_expiry)}
                    </p>
                    <StatusBadge status={item.status} />
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => decrement(item)}
                      disabled={item.quantity <= 0 || item.is_finished}
                      className="w-9 h-9 flex items-center justify-center rounded-full text-sm disabled:opacity-20"
                      style={{ background: "var(--surface)", color: "var(--muted)" }}
                      aria-label={`Decrease ${item.name} quantity`}
                    >−</button>
                    {!item.is_finished && (
                      <button
                        onClick={() => finish(item)}
                        className="w-9 h-9 flex items-center justify-center rounded-full text-sm"
                        style={{ background: "var(--accent-light)", color: "var(--accent)" }}
                        aria-label={`Mark ${item.name} as finished`}
                      >✓</button>
                    )}
                    <button
                      onClick={() => remove(item.id)}
                      className="w-9 h-9 flex items-center justify-center rounded-full text-xs"
                      style={{ background: "var(--surface)", color: "var(--faint)" }}
                      aria-label={`Delete ${item.name}`}
                    >×</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      <Nav />
    </>
  );
}
