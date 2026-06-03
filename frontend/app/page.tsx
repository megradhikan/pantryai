"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function AuthPage() {
  const [tab, setTab] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (tab === "signup") {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setError("Check your email to confirm your account.");
        setLoading(false);
        return;
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.push("/dashboard");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[100dvh] flex flex-col items-center justify-center px-6" style={{ background: "var(--bg)" }}>
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <div
            className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center text-3xl"
            style={{ background: "var(--primary-light)" }}
          >
            🥬
          </div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--ink)" }}>PantryAI</h1>
          <p className="text-sm mt-1" style={{ color: "var(--muted)" }}>Track food, reduce waste, cook smarter</p>
        </div>

        <div className="flex p-1 mb-8" style={{ background: "var(--surface)", borderRadius: "var(--radius-md)" }}>
          {(["signin", "signup"] as const).map((t) => (
            <button
              key={t}
              className="flex-1 py-2.5 text-sm font-semibold transition-all"
              style={{
                borderRadius: "var(--radius-sm)",
                background: tab === t ? "var(--bg)" : "transparent",
                color: tab === t ? "var(--ink)" : "var(--muted)",
                boxShadow: tab === t ? "var(--shadow-sm)" : "none",
              }}
              onClick={() => setTab(t)}
            >
              {t === "signin" ? "Sign In" : "Sign Up"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="email" required value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
            placeholder="Email address"
          />
          <input
            type="password" required value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
            placeholder="Password"
          />
          {error && (
            <p className="text-sm text-center" style={{ color: error.startsWith("Check") ? "var(--success)" : "var(--danger)" }}>
              {error}
            </p>
          )}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "..." : tab === "signin" ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
