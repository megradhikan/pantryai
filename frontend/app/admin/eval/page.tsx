"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import Nav from "@/components/Nav";

const ADMIN_EMAIL = process.env.NEXT_PUBLIC_ADMIN_EMAIL;

export default function EvalPage() {
  const [authorized, setAuthorized] = useState(false);
  const [receiptStats, setReceiptStats] = useState<Record<string, unknown> | null>(null);
  const [recipeStats, setRecipeStats] = useState<Record<string, unknown> | null>(null);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) { router.push("/"); return; }
      if (ADMIN_EMAIL && session.user.email === ADMIN_EMAIL) {
        setAuthorized(true);
        Promise.all([api.receipts.evalSummary(), api.recipes.eval()]).then(([r, s]) => {
          setReceiptStats(r); setRecipeStats(s as Record<string, unknown>);
        });
      }
    });
  }, []);

  if (!authorized) {
    return (
      <>
        <div className="page flex items-center justify-center">
          <p className="text-sm" style={{ color: "var(--muted)" }}>Admin access only.</p>
        </div>
        <Nav />
      </>
    );
  }

  return (
    <>
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Eval Dashboard</h1>
        </div>
        <div className="page-body space-y-4">
          <StatCard title="Receipt Extraction" data={receiptStats} fields={[
            ["total_receipts", "Total Receipts"],
            ["parse_success_rate", "Parse Rate", true],
            ["avg_items_per_receipt", "Avg Items"],
          ]} />
          <StatCard title="Recipe Suggestions" data={recipeStats} fields={[
            ["total_suggestions", "Total Sets"],
            ["avg_match_score", "Avg Match", true],
            ["led_to_shopping_list_pct", "Led to shopping list", true],
          ]} />
        </div>
      </div>
      <Nav />
    </>
  );
}

function StatCard({ title, data, fields }: { title: string; data: Record<string, unknown> | null; fields: [string, string, boolean?][] }) {
  return (
    <div className="card">
      <h2 className="text-sm font-semibold mb-3" style={{ color: "var(--ink)" }}>{title}</h2>
      {!data ? (
        <p className="text-xs" style={{ color: "var(--faint)" }}>Loading...</p>
      ) : (
        <div className="space-y-2.5">
          {fields.map(([key, label, isPct]) => (
            <div key={key} className="flex justify-between text-sm">
              <span style={{ color: "var(--muted)" }}>{label}</span>
              <span className="font-medium" style={{ color: "var(--ink)" }}>
                {isPct ? `${(Number(data[key] ?? 0) * 100).toFixed(1)}%` : String(data[key] ?? 0)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
