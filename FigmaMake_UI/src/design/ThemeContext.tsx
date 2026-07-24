import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type ThemeChoice = "light" | "dark" | "system";

type ThemeValue = { theme: ThemeChoice; resolved: "light" | "dark"; setTheme: (theme: ThemeChoice) => void };
const ThemeContext = createContext<ThemeValue | null>(null);

function themeFromUrl(): ThemeChoice {
  const value = new URLSearchParams(window.location.search).get("theme");
  return value === "light" || value === "dark" || value === "system" ? value : "system";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<ThemeChoice>(themeFromUrl);
  const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  const resolved = theme === "system" ? (prefersDark ? "dark" : "light") : theme;

  useEffect(() => {
    document.documentElement.dataset.theme = resolved;
    document.documentElement.style.colorScheme = resolved;
  }, [resolved]);

  const value = useMemo(() => ({ theme, resolved, setTheme }), [theme, resolved]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useTheme must be used inside ThemeProvider");
  return value;
}
