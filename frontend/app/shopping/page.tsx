"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import type { ShoppingList } from "@/lib/types";
import Nav from "@/components/Nav";

export default function ShoppingPage() {
  const [lists, setLists] = useState<ShoppingList[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) router.push("/");
      else load();
    });
  }, []);

  async function load() {
    try { setLists(await api.shopping.list()); }
    finally { setLoading(false); }
  }

  async function toggleItem(listId: string, itemName: string) {
    const r = await api.shopping.toggleItem(listId, itemName);
    setLists((p) => p.map((l) => (l.id === listId ? { ...l, items: r.items } : l)));
  }

  function clearChecked(listId: string) {
    setLists((p) => p.map((l) => l.id === listId ? { ...l, items: l.items.filter((i) => !i.checked) } : l));
  }

  return (
    <>
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Shopping Lists</h1>
        </div>

        <div className="page-body">
          {loading ? (
            <div className="space-y-4">
              {[...Array(2)].map((_, i) => (
                <div key={i} className="card">
                  <div className="flex items-center justify-between mb-3">
                    <div className="space-y-2 flex-1">
                      <div className="skeleton" style={{ height: 14, width: "55%" }} />
                      <div className="skeleton" style={{ height: 11, width: "35%" }} />
                    </div>
                  </div>
                  <div className="skeleton" style={{ height: 4, borderRadius: "var(--radius-full)", marginBottom: "0.75rem" }} />
                  {[...Array(3)].map((_, j) => (
                    <div key={j} className="flex items-center gap-3 py-2">
                      <div className="skeleton" style={{ width: 20, height: 20, borderRadius: "50%", flexShrink: 0 }} />
                      <div className="skeleton" style={{ height: 13, flex: 1 }} />
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : lists.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-4xl mb-3 opacity-60">🛒</div>
              <p className="text-sm" style={{ color: "var(--muted)" }}>No shopping lists yet. Generate one from the Recipes page.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {lists.map((list) => {
                const checked = list.items.filter((i) => i.checked).length;
                const total = list.items.length;
                const pct = total > 0 ? (checked / total) * 100 : 0;
                return (
                  <div key={list.id} className="card">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h2 className="text-sm font-semibold" style={{ color: "var(--ink)" }}>{list.recipe_title}</h2>
                        <p className="text-xs" style={{ color: "var(--muted)" }}>
                          {checked}/{total} done · {new Date(list.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {checked > 0 && (
                        <button onClick={() => clearChecked(list.id)}
                          className="text-xs font-medium" style={{ color: "var(--danger)" }}>
                          Clear done
                        </button>
                      )}
                    </div>

                    {/* Progress */}
                    <div className="h-1.5 rounded-full mb-3 overflow-hidden" style={{ background: "var(--surface)" }}>
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${pct}%`,
                          background: pct >= 100 ? "var(--success)" : "var(--accent)",
                          boxShadow: pct >= 100 ? "0 0 6px oklch(0.60 0.15 145 / 0.45)" : "none",
                          transition: "width 350ms cubic-bezier(0.25, 1, 0.5, 1), background 350ms ease-out, box-shadow 350ms ease-out",
                          animation: pct >= 100 ? "progressGlow 1.2s ease-in-out 1" : "none",
                        }}
                      />
                    </div>

                    {total === 0 ? (
                      <p className="text-xs text-center py-2" style={{ color: "var(--faint)" }}>All items cleared.</p>
                    ) : (
                      <div className="space-y-0.5">
                        {list.items.map((item) => (
                          <button
                            key={item.name}
                            onClick={() => toggleItem(list.id, item.name)}
                            className="w-full flex items-center gap-3 py-2.5 px-3 rounded-xl text-left transition-colors"
                            style={{ minHeight: 44 }}
                          >
                            <div
                              className="w-5 h-5 rounded-full flex items-center justify-center shrink-0"
                              style={{
                                border: item.checked ? "none" : "2px solid var(--faint)",
                                background: item.checked ? "var(--accent)" : "transparent",
                                transition: "background 200ms ease-out, border-color 200ms ease-out, transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1)",
                                transform: "scale(1)",
                              }}
                            >
                              {item.checked && (
                                <span
                                  className="text-white text-xs"
                                  style={{ animation: "checkPop 220ms cubic-bezier(0.34, 1.56, 0.64, 1) both" }}
                                >✓</span>
                              )}
                            </div>
                            <span className="text-sm flex-1" style={{
                              textDecoration: item.checked ? "line-through" : "none",
                              color: item.checked ? "var(--faint)" : "var(--ink)",
                            }}>
                              {item.name}
                            </span>
                            {item.quantity != null && (
                              <span className="text-xs" style={{ color: "var(--muted)" }}>
                                {item.quantity}{item.unit ? ` ${item.unit}` : ""}
                              </span>
                            )}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
      <Nav />
    </>
  );
}
