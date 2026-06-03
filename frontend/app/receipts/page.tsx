"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import type { ExtractedItem, Receipt } from "@/lib/types";
import Nav from "@/components/Nav";

const CATEGORIES = ["Dairy", "Protein", "Produce", "Grains", "Snacks", "Beverages", "Frozen", "Condiments", "Other"];

const SCAN_MESSAGES = [
  "Reading your receipt...",
  "Picking out the grocery items...",
  "Sorting into categories...",
  "Estimating expiry dates...",
  "Almost ready...",
];

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [uploading, setUploading] = useState(false);
  const [scanMsgIdx, setScanMsgIdx] = useState(0);
  const [extractedItems, setExtractedItems] = useState<ExtractedItem[] | null>(null);
  const [pendingReceiptId, setPendingReceiptId] = useState<string | null>(null);
  const [purchaseDate, setPurchaseDate] = useState(new Date().toISOString().split("T")[0]);
  const [error, setError] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (!uploading) { setScanMsgIdx(0); return; }
    const t = setInterval(() => setScanMsgIdx((i) => (i + 1) % SCAN_MESSAGES.length), 2200);
    return () => clearInterval(t);
  }, [uploading]);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) router.push("/");
      else loadReceipts();
    });
  }, []);

  async function loadReceipts() { try { setReceipts(await api.receipts.list()); } catch {} }

  async function handleFile(file: File) {
    setError("");
    if (file.size > 10 * 1024 * 1024) { setError("File exceeds 10MB"); return; }
    const ok = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
    if (!ok.includes(file.type)) { setError("JPEG, PNG, WebP, or PDF only"); return; }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("purchase_date", purchaseDate);
    setUploading(true); setExtractedItems(null); setPendingReceiptId(null); setConfirmed(false);
    try {
      const r = await api.receipts.upload(fd);
      setExtractedItems(r.items); setPendingReceiptId(r.receipt_id);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Upload failed"); }
    finally { setUploading(false); }
  }

  function updateItem(i: number, f: keyof ExtractedItem, v: string | number) {
    if (!extractedItems) return;
    const u = [...extractedItems]; u[i] = { ...u[i], [f]: v }; setExtractedItems(u);
  }

  async function confirmItems() {
    if (!pendingReceiptId || !extractedItems) return;
    try {
      await api.receipts.confirm(pendingReceiptId, extractedItems);
      setConfirmed(true); setExtractedItems(null); setPendingReceiptId(null); loadReceipts();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Failed"); }
  }

  return (
    <>
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Scan Receipt</h1>
        </div>

        <div className="page-body">
          <div
            className="card flex flex-col items-center justify-center mb-4"
            style={{
              border: uploading ? "1px solid var(--primary-light)" : "1px dashed var(--faint)",
              cursor: uploading ? "default" : "pointer",
              paddingTop: "2.5rem",
              paddingBottom: "2.5rem",
              transition: "border-color 250ms ease-out",
            }}
            onClick={() => !uploading && fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); !uploading && e.dataTransfer.files[0] && handleFile(e.dataTransfer.files[0]); }}
          >
            <input ref={fileInputRef} type="file" className="hidden"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
            {uploading ? (
              <>
                {/* Scan zone */}
                <div style={{
                  position: "relative",
                  width: 56,
                  height: 72,
                  borderRadius: 6,
                  border: "2px solid var(--primary)",
                  marginBottom: "1rem",
                  overflow: "hidden",
                  background: "var(--primary-light)",
                }}>
                  {/* Scan line */}
                  <div style={{
                    position: "absolute",
                    left: 0,
                    right: 0,
                    height: 2,
                    background: "linear-gradient(90deg, transparent, var(--primary), transparent)",
                    animation: "scanSweep 1.6s ease-in-out infinite",
                    boxShadow: "0 0 8px var(--primary)",
                  }} />
                  {/* Receipt lines */}
                  {[20, 35, 50, 65, 80].map((pct) => (
                    <div key={pct} style={{
                      position: "absolute",
                      left: "15%",
                      right: "15%",
                      top: `${pct}%`,
                      height: 1.5,
                      borderRadius: 1,
                      background: "var(--primary)",
                      opacity: 0.25,
                    }} />
                  ))}
                </div>
                <p className="text-sm font-semibold" style={{ color: "var(--primary)", minHeight: "1.25rem" }}>
                  {SCAN_MESSAGES[scanMsgIdx]}
                </p>
              </>
            ) : (
              <>
                <div className="text-3xl mb-2">📷</div>
                <p className="text-sm font-semibold" style={{ color: "var(--ink)" }}>Tap to scan receipt</p>
                <p className="text-xs mt-1" style={{ color: "var(--faint)" }}>JPEG, PNG, WebP, PDF · up to 10MB</p>
              </>
            )}
          </div>

          <div className="card flex items-center justify-between mb-4">
            <span className="text-xs font-medium" style={{ color: "var(--muted)" }}>Purchase date</span>
            <input type="date" value={purchaseDate} onChange={(e) => setPurchaseDate(e.target.value)}
              className="text-sm text-right bg-transparent" style={{ color: "var(--ink)" }} />
          </div>

          {error && <p className="text-xs text-center mb-3" style={{ color: "var(--danger)" }}>{error}</p>}
          {confirmed && (
            <div className="card mb-4 text-center success-enter" style={{ background: "var(--accent-light)" }}>
              <p className="text-sm font-semibold" style={{ color: "var(--accent)" }}>
                Items added to your pantry
              </p>
            </div>
          )}

          {extractedItems && (
            <div className="card mb-4 success-enter">
              <h2 className="text-sm font-semibold mb-3" style={{ color: "var(--ink)" }}>
                Review Items ({extractedItems.length})
              </h2>
              <div className="space-y-2">
                {extractedItems.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-3" style={{ background: "var(--surface)", borderRadius: "var(--radius-md)" }}>
                    <div className="flex-1 min-w-0">
                      <input value={item.name} onChange={(e) => updateItem(idx, "name", e.target.value)}
                        className="w-full text-sm font-medium bg-transparent focus:outline-none" style={{ color: "var(--ink)" }} />
                      <div className="flex gap-2 mt-1">
                        <input type="number" value={item.quantity} onChange={(e) => updateItem(idx, "quantity", parseFloat(e.target.value))}
                          className="w-14 text-xs bg-transparent" style={{ color: "var(--muted)" }} />
                        <select value={item.category} onChange={(e) => updateItem(idx, "category", e.target.value)}
                          className="text-xs bg-transparent" style={{ color: "var(--muted)" }}>
                          {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                        </select>
                      </div>
                    </div>
                    <button onClick={() => setExtractedItems(extractedItems.filter((_, i) => i !== idx))}
                      className="px-2 text-lg" style={{ color: "var(--faint)" }}>×</button>
                  </div>
                ))}
              </div>
              <button onClick={() => setExtractedItems([...extractedItems, { name: "", quantity: 1, unit: null, category: "Other" }])}
                className="w-full text-xs font-medium py-2 mt-2" style={{ color: "var(--primary)" }}>
                + Add row
              </button>
              <button onClick={confirmItems} className="btn-primary w-full mt-3">Confirm and add to pantry</button>
            </div>
          )}

          {receipts.length > 0 && (
            <>
              <p className="text-xs font-semibold mb-2 px-1" style={{ color: "var(--muted)" }}>Past Receipts</p>
              <div className="space-y-2">
                {receipts.map((r) => (
                  <div key={r.id} className="card flex justify-between items-center">
                    <div>
                      <p className="text-sm font-medium" style={{ color: "var(--ink)" }}>{r.store_name ?? "Unknown Store"}</p>
                      <p className="text-xs" style={{ color: "var(--muted)" }}>{r.purchase_date}</p>
                    </div>
                    <span className="chip chip-muted">{r.extraction_metadata?.item_count ?? 0} items</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
      <Nav />
    </>
  );
}
