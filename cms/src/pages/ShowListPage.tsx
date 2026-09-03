import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";

const SECTIONS = ["kids", "family", "originals", "documentaries", "movies"];
const STATUSES = ["draft", "published"];

export default function ShowListPage() {
  const [q, setQ] = useState("");
  const [section, setSection] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useQuery({
    queryKey: ["shows", q, section, status, page],
    queryFn: () => api.listShows({ q, section, status, page, page_size: pageSize }),
  });

  if (error) {
    const apiErr = error as ApiError;
    return (
      <div>
        <h2>Shows</h2>
        <div className="error-banner">
          {apiErr.status === 401
            ? "You're not signed in. Add an API key on the Settings page."
            : apiErr.message}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="toolbar">
        <h2 style={{ margin: 0, marginRight: "auto" }}>Shows</h2>
        <Link to="/shows/new" className="btn btn-primary">+ New show</Link>
      </div>

      <div className="toolbar">
        <input placeholder="Search titles…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} style={{ maxWidth: 240 }} />
        <select value={section} onChange={(e) => { setSection(e.target.value); setPage(1); }} style={{ maxWidth: 180 }}>
          <option value="">All sections</option>
          {SECTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} style={{ maxWidth: 160 }}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {isLoading && <div className="empty-state">Loading shows…</div>}

      {!isLoading && data?.items?.length === 0 && (
        <div className="empty-state">No shows match your filters yet.</div>
      )}

      {!isLoading && data?.items?.length > 0 && (
        <>
          <table>
            <thead>
              <tr><th>Title</th><th>Category</th><th>Section</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {data.items.map((show: any) => (
                <tr key={show.id}>
                  <td><Link to={`/shows/${show.id}`}>{show.title}</Link></td>
                  <td>{show.category || "—"}</td>
                  <td>{show.section || "—"}</td>
                  <td><span className={`badge badge-${show.status}`}>{show.status}</span></td>
                  <td><Link to={`/shows/${show.id}`} className="btn">Edit</Link></td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="toolbar" style={{ marginTop: 14 }}>
            <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>← Prev</button>
            <span>Page {page} of {Math.max(1, Math.ceil((data.total || 0) / pageSize))}</span>
            <button
              className="btn"
              disabled={page * pageSize >= (data.total || 0)}
              onClick={() => setPage((p) => p + 1)}
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
