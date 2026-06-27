import { useEffect, useRef, useState } from "react";

// Mermaid được import ĐỘNG (chỉ tải ~khi có sơ đồ) -> tách thành chunk riêng, giữ bundle nhẹ
// cho trải nghiệm on-prem/offline. Theme bám dark/light hiện tại.
let _seq = 0;

export function MermaidBlock({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: document.documentElement.classList.contains("dark") ? "dark" : "default",
        });
        const { svg } = await mermaid.render(`mmd-${++_seq}`, chart.trim());
        if (!cancelled && ref.current) ref.current.innerHTML = svg;
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Lỗi sơ đồ");
      }
    })();
    return () => { cancelled = true; };
  }, [chart]);

  if (err) return <pre className="text-xs text-destructive">Mermaid: {err}</pre>;
  return <div ref={ref} className="my-2 flex justify-center overflow-x-auto" />;
}
