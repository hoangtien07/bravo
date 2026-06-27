import { useState } from "react";
import { Moon, Sun } from "lucide-react";
import { getTheme, toggleTheme, type Theme } from "@/lib/theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(getTheme());
  return (
    <button
      onClick={() => setTheme(toggleTheme())}
      className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
      aria-label="Đổi giao diện sáng/tối"
    >
      {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
      {theme === "dark" ? "Sáng" : "Tối"}
    </button>
  );
}
