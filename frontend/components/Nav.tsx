"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/dashboard", label: "Pantry", icon: (active: boolean) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--primary)" : "var(--faint)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
  )},
  { href: "/receipts", label: "Scan", icon: (active: boolean) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--primary)" : "var(--faint)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="7" y1="8" x2="17" y2="8"/><line x1="7" y1="12" x2="17" y2="12"/><line x1="7" y1="16" x2="13" y2="16"/></svg>
  )},
  { href: "/recipes", label: "Recipes", icon: (active: boolean) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--primary)" : "var(--faint)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a7 7 0 0 1 7 7c0 2.5-1.5 5-3 6.5V18H8v-2.5C6.5 14 5 11.5 5 9a7 7 0 0 1 7-7z"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="9" y1="18" x2="15" y2="18"/></svg>
  )},
  { href: "/shopping", label: "Shop", icon: (active: boolean) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--primary)" : "var(--faint)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
  )},
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0"
      style={{
        zIndex: "var(--z-tab-bar)" as string,
        paddingBottom: "var(--safe-bottom)",
        background: "oklch(1 0 0 / 0.85)",
        backdropFilter: "blur(20px) saturate(180%)",
        WebkitBackdropFilter: "blur(20px) saturate(180%)",
        borderTop: "1px solid oklch(0 0 0 / 0.06)",
      }}
    >
      <div className="flex items-center justify-around" style={{ height: "var(--tab-height)" }}>
        {tabs.map((t) => {
          const active = pathname.startsWith(t.href);
          return (
            <Link
              key={t.href}
              href={t.href}
              className="flex flex-col items-center justify-center gap-0.5 min-w-[3rem] min-h-[2.75rem]"
              style={{ color: active ? "var(--primary)" : "var(--faint)" }}
            >
              {t.icon(active)}
              <span className="text-[10px] font-medium leading-none">{t.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
