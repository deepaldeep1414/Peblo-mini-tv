import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import PosterCard from "../components/PosterCard";

export default function SearchPage() {
  const [params] = useSearchParams();
  const initialQ = params.get("q") || "";
  const [q, setQ] = useState(initialQ);
  const [category, setCategory] = useState("");
  const [language, setLanguage] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["search", q, category, language],
    queryFn: () => api.search({ q, category, language }),
  });

  const categories = useMemo(
    () => Array.from(new Set((data?.results || []).map((r: any) => r.show.category).filter(Boolean))),
    [data]
  );

  return (
    <div style={{ padding: "20px 32px" }}>
      <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
        <input
          placeholder="Search…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ maxWidth: 260, padding: "8px 12px", borderRadius: 6, border: "none", background: "#1c1c22", color: "#fff" }}
        />
        <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{ padding: "8px 10px", borderRadius: 6, border: "none", background: "#1c1c22", color: "#fff" }}>
          <option value="">All languages</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
        </select>
      </div>

      {isLoading && <div className="empty-state">Searching…</div>}
      {error && <div className="empty-state">Something went wrong loading results. Try again in a moment.</div>}

      {!isLoading && !error && (data?.results?.length ?? 0) === 0 && (
        <div className="empty-state">
          No shows match {q ? `"${q}"` : "your filters"}. Try a different search or clear the filters.
        </div>
      )}

      <div className="row-track" style={{ padding: 0, flexWrap: "wrap" }}>
        {data?.results?.map((r: any) => (
          <PosterCard key={r.show.id} id={r.show.id} title={r.show.title} posterKey={r.show.poster_key} />
        ))}
      </div>
    </div>
  );
}
