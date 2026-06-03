"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import type { RecipeSuggestion } from "@/lib/types";
import Nav from "@/components/Nav";

interface GeneratedRecipe {
  title: string;
  ingredients: { name: string; quantity: number | null; unit: string | null; from_pantry: boolean }[];
  instructions: string;
  cuisine: string;
  prep_time_mins: number;
  pantry_items_used: string[];
  extra_items_needed: { name: string; quantity: number | null; unit: string | null }[];
}
interface MissingItem { name: string; quantity?: number | null; unit?: string | null; }

function MissingChip({ item, onHaveIt, onBuyIt }: { item: MissingItem; onHaveIt: () => void; onBuyIt: () => void }) {
  const [status, setStatus] = useState<"" | "added" | "buying">("");
  if (status === "added") return <span className="chip chip-success">Added: {item.name}</span>;
  if (status === "buying") return <span className="chip chip-accent">To buy: {item.name}</span>;
  return (
    <span className="chip chip-danger inline-flex items-center gap-1.5">
      {item.name}
      <button onClick={() => { onHaveIt(); setStatus("added"); }}
        className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
        style={{ background: "var(--accent-light)", color: "var(--accent)" }}
        aria-label={`Mark ${item.name} as in pantry`}>✓</button>
      <button onClick={() => { onBuyIt(); setStatus("buying"); }}
        className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
        style={{ background: "var(--primary-light)", color: "var(--primary)" }}
        aria-label={`Add ${item.name} to shopping list`}>+</button>
    </span>
  );
}

export default function RecipesPage() {
  const [suggestions, setSuggestions] = useState<RecipeSuggestion[]>([]);
  const [generated, setGenerated] = useState<GeneratedRecipe | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [toBuy, setToBuy] = useState<Record<string, MissingItem[]>>({});
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => { if (!session) router.push("/"); });
  }, []);

  async function getSuggestions() {
    setLoading(true); setError("");
    try { setSuggestions((await api.recipes.suggest()).suggestions); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Failed"); }
    finally { setLoading(false); }
  }
  async function generateRecipe() {
    setGenerating(true); setError("");
    try { setGenerated((await api.recipes.generate()).recipe); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Failed"); }
    finally { setGenerating(false); }
  }
  async function addToPantry(item: MissingItem) {
    try { await api.inventory.addManual({ name: item.name, category: "Other", quantity: item.quantity ?? 1, unit: item.unit ?? undefined }); } catch {}
  }
  function markToBuy(key: string, item: MissingItem) {
    setToBuy((p) => ({ ...p, [key]: [...(p[key] || []), item] }));
  }
  async function createList(key: string, title: string) {
    if (!toBuy[key]?.length) return;
    try {
      await api.shopping.create(title, toBuy[key]);
      setToBuy((p) => { const n = { ...p }; delete n[key]; return n; });
      router.push("/shopping");
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Failed"); }
  }

  return (
    <>
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Recipes</h1>
        </div>

        <div className="page-body">
          <div className="flex gap-3 mb-5">
            <button onClick={generateRecipe} disabled={generating} className="btn-primary flex-1">
              {generating ? "Creating..." : "Generate recipe"}
            </button>
            <button onClick={getSuggestions} disabled={loading} className="btn-accent flex-1">
              {loading ? "Finding..." : "Match recipes"}
            </button>
          </div>

          {error && <p className="text-xs text-center mb-3" style={{ color: "var(--danger)" }}>{error}</p>}

          {/* Generated */}
          {generated && (
            <div className="card mb-4" style={{ background: "var(--primary-light)" }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="chip" style={{ background: "var(--primary)", color: "white", fontSize: "0.625rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.04em" }}>AI Generated</span>
                <span className="text-xs" style={{ color: "var(--muted)" }}>{generated.cuisine} · {generated.prep_time_mins} min</span>
              </div>
              <h3 className="text-base font-bold mb-3" style={{ color: "var(--ink)" }}>{generated.title}</h3>

              <p className="text-xs font-semibold mb-2" style={{ color: "var(--muted)" }}>Ingredients</p>
              <div className="space-y-1 mb-4">
                {generated.ingredients.map((ing) => (
                  <div key={ing.name} className="flex items-center gap-2 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full shrink-0"
                      style={{ background: ing.from_pantry ? "var(--status-fresh)" : "var(--status-expired)" }} />
                    <span style={{ color: "var(--ink)" }}>{ing.name}</span>
                    {ing.quantity && <span className="text-xs" style={{ color: "var(--muted)" }}>{ing.quantity}{ing.unit ? ` ${ing.unit}` : ""}</span>}
                  </div>
                ))}
              </div>

              <p className="text-xs font-semibold mb-2" style={{ color: "var(--muted)" }}>Instructions</p>
              <p className="text-sm mb-4 whitespace-pre-line" style={{ color: "var(--ink)", lineHeight: 1.6 }}>{generated.instructions}</p>

              {generated.extra_items_needed.length > 0 && (
                <div style={{ borderTop: "1px solid oklch(0 0 0 / 0.06)", paddingTop: "0.75rem" }}>
                  <p className="text-xs font-semibold mb-2" style={{ color: "var(--muted)" }}>Missing</p>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {generated.extra_items_needed.map((m) => (
                      <MissingChip key={m.name} item={m} onHaveIt={() => addToPantry(m)} onBuyIt={() => markToBuy("generated", m)} />
                    ))}
                  </div>
                  {(toBuy["generated"]?.length ?? 0) > 0 && (
                    <button onClick={() => createList("generated", generated.title)} className="btn-primary w-full">
                      Create shopping list ({toBuy["generated"].length})
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Empty */}
          {suggestions.length === 0 && !generated && !loading && !generating && (
            <div className="text-center py-16">
              <div className="text-4xl mb-3 opacity-60">🍳</div>
              <p className="text-sm" style={{ color: "var(--muted)" }}>Generate a custom recipe or find matches from the database.</p>
            </div>
          )}

          {/* RAG */}
          {suggestions.length > 0 && (
            <p className="text-xs font-semibold mb-2 px-1" style={{ color: "var(--muted)" }}>Database Matches</p>
          )}
          <div className="space-y-3">
            {suggestions.map((s) => (
              <div key={s.recipe_id} className="card">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-semibold" style={{ color: "var(--ink)" }}>{s.title}</h3>
                  <span className="chip chip-success shrink-0 ml-2">{Math.round(s.match_score * 100)}%</span>
                </div>
                <p className="text-xs mb-2" style={{ color: "var(--muted)" }}>
                  {s.inventory_items_used.length} / {s.inventory_items_used.length + s.missing_ingredients.length} ingredients
                </p>
                {s.inventory_items_used.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {s.inventory_items_used.map((n) => <span key={n} className="chip chip-success">{n}</span>)}
                  </div>
                )}
                {s.missing_ingredients.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {s.missing_ingredients.map((m) => (
                      <MissingChip key={m.name} item={m} onHaveIt={() => addToPantry(m)} onBuyIt={() => markToBuy(s.recipe_id, m)} />
                    ))}
                  </div>
                )}
                {(toBuy[s.recipe_id]?.length ?? 0) > 0 && (
                  <button onClick={() => createList(s.recipe_id, s.title)} className="btn-primary w-full">
                    Create shopping list ({toBuy[s.recipe_id].length})
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
      <Nav />
    </>
  );
}
