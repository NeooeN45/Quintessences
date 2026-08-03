"use client";

type Politeness = "polite" | "assertive";

export function announce(message: string, politeness: Politeness = "polite"): void {
  if (typeof window === "undefined") return;

  const id = politeness === "assertive" ? "sr-announcer-assertive" : "sr-announcer-polite";
  const el = document.getElementById(id);
  if (!el) return;

  // Clear puis re-set pour forcer la re-annonce
  el.textContent = "";
  setTimeout(() => {
    el.textContent = message;
  }, 50);
}
