import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmtMoney(v: string | number | undefined | null): string {
  const n = Number(v);
  return isNaN(n) ? String(v ?? "") : n.toLocaleString("vi-VN");
}

export function fmtDate(s?: string | null): string {
  if (!s) return "";
  try {
    return new Date(s).toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" });
  } catch {
    return s;
  }
}
