import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import ArtworkUploadSlot from "../components/ArtworkUploadSlot";

const SECTIONS = ["kids", "family", "originals", "documentaries", "movies"];

export default function ShowEditPage() {
  const { showId } = useParams();
  const isNew = !showId;
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: show, isLoading, error } = useQuery({
    queryKey: ["show", showId],
    queryFn: () => api.getShow(showId!),
    enabled: !isNew,
  });

  const [form, setForm] = useState({ title: "", synopsis: "", category: "", section: "" });
  const activeForm = isNew ? form : { title: show?.title ?? "", synopsis: show?.synopsis ?? "", category: show?.category ?? "", section: show?.section ?? "" };

  const [formError, setFormError] = useState<string | null>(null);

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (isNew) {
        const created = await api.createShow(form);
        return created;
      }
      return api.updateShow(showId!, activeForm);
    },
    onSuccess: (data) => {
      setFormError(null);
      qc.invalidateQueries({ queryKey: ["shows"] });
      if (isNew) navigate(`/shows/${data.id}`);
      else qc.invalidateQueries({ queryKey: ["show", showId] });
    },
    onError: (err) => setFormError(err instanceof ApiError ? err.message : "Could not save show."),
  });

  const publishToggle = useMutation({
    mutationFn: (status: string) => api.updateShow(showId!, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["show", showId] }),
    onError: (err) => setFormError(err instanceof ApiError ? err.message : "Could not update status."),
  });

  const addSeason = useMutation({
    mutationFn: (number: number) => api.createSeason({ show_id: showId, number }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["show", showId] }),
  });

  const addEpisode = useMutation({
    mutationFn: (vars: { seasonId: string; title: string; language: string }) =>
      api.createEpisode({ season_id: vars.seasonId, title: vars.title, language: vars.language, episode_number: 1 }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["show", showId] }),
  });

  if (!isNew && isLoading) return <div className="empty-state">Loading show…</div>;
  if (!isNew && error) {
    const apiErr = error as ApiError;
    return <div className="error-banner">{apiErr.status === 404 ? "Show not found." : apiErr.message}</div>;
  }

  return (
    <div>
      <h2>{isNew ? "New show" : show.title}</h2>
      {formError && <div className="error-banner">{formError}</div>}

      <div className="card" style={{ maxWidth: 560 }}>
        <div className="field">
          <label>Title</label>
          <input
            value={activeForm.title}
            onChange={(e) => isNew ? setForm({ ...form, title: e.target.value }) : (show.title = e.target.value)}
            onBlur={(e) => !isNew && saveMutation.mutate()}
            defaultValue={activeForm.title}
          />
        </div>
        <div className="field">
          <label>Synopsis</label>
          <textarea
            rows={3}
            defaultValue={activeForm.synopsis}
            onBlur={(e) => {
              if (isNew) setForm({ ...form, synopsis: e.target.value });
              else api.updateShow(showId!, { synopsis: e.target.value }).then(() => qc.invalidateQueries({ queryKey: ["show", showId] }));
            }}
          />
        </div>
        <div className="field">
          <label>Category</label>
          <input
            defaultValue={activeForm.category}
            onBlur={(e) => {
              if (isNew) setForm({ ...form, category: e.target.value });
              else api.updateShow(showId!, { category: e.target.value }).then(() => qc.invalidateQueries({ queryKey: ["show", showId] }));
            }}
          />
        </div>
        <div className="field">
          <label>Section (required to publish)</label>
          <select
            defaultValue={activeForm.section}
            onChange={(e) => {
              if (isNew) setForm({ ...form, section: e.target.value });
              else api.updateShow(showId!, { section: e.target.value }).then(() => qc.invalidateQueries({ queryKey: ["show", showId] }));
            }}
          >
            <option value="">— choose —</option>
            {SECTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {isNew ? (
          <button className="btn btn-primary" disabled={!form.title || saveMutation.isPending} onClick={() => saveMutation.mutate()}>
            Create show
          </button>
        ) : (
          <div className="toolbar">
            <span className={`badge badge-${show.status}`}>{show.status}</span>
            {show.status === "draft" ? (
              <button className="btn btn-primary" onClick={() => publishToggle.mutate("published")}>Mark as published</button>
            ) : (
              <button className="btn" onClick={() => publishToggle.mutate("draft")}>Revert to draft</button>
            )}
          </div>
        )}
      </div>

      {!isNew && (
        <>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Show artwork</h3>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              <ArtworkUploadSlot kind="poster" showId={showId} existing={show.artworks?.find((a: any) => a.kind === "poster")} />
              <ArtworkUploadSlot kind="banner" showId={showId} existing={show.artworks?.find((a: any) => a.kind === "banner")} />
            </div>
          </div>

          <div className="card">
            <div className="toolbar">
              <h3 style={{ margin: 0, marginRight: "auto" }}>Seasons & episodes</h3>
              <button
                className="btn"
                onClick={() => {
                  const nextNum = show.seasons?.length
                    ? Math.max(...show.seasons.map((s: any) => s.number)) + 1
                    : 1;
                  addSeason.mutate(nextNum);
                }}
              >
                + Add season
              </button>
              <button className="btn" onClick={() => addSeason.mutate(0)}>
                + Add trailers (Season 0)
              </button>
            </div>

            {(!show.seasons || show.seasons.length === 0) && (
              <div className="empty-state">No seasons yet. Add one above.</div>
            )}

            {show.seasons?.sort((a: any, b: any) => a.number - b.number).map((season: any) => (
              <SeasonBlock key={season.id} season={season} onAddEpisode={(t, l) => addEpisode.mutate({ seasonId: season.id, title: t, language: l })} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function SeasonBlock({ season, onAddEpisode }: { season: any; onAddEpisode: (title: string, lang: string) => void }) {
  const [title, setTitle] = useState("");
  const [lang, setLang] = useState("en");
  const [showAdd, setShowAdd] = useState(false);
  const qc = useQueryClient();

  const updateEp = useMutation({
    mutationFn: (vars: { id: string; body: any }) => api.updateEpisode(vars.id, vars.body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["show"] }),
  });

  return (
    <div style={{ marginBottom: 18, paddingLeft: 4, borderLeft: "3px solid #eceef1" }}>
      <div style={{ fontWeight: 600, marginBottom: 6, paddingLeft: 10 }}>
        {season.number === 0 ? "Trailers (Season 0)" : `Season ${season.number}`}
      </div>
      <table>
        <thead><tr><th>Title</th><th>Language</th><th>Duration (s)</th><th>Status</th><th>Thumbnail</th></tr></thead>
        <tbody>
          {season.episodes?.map((ep: any) => (
            <tr key={ep.id}>
              <td>{ep.title}</td>
              <td>{ep.language}</td>
              <td>
                <input
                  type="number" defaultValue={ep.duration_seconds ?? ""} style={{ width: 90 }}
                  onBlur={(e) => updateEp.mutate({ id: ep.id, body: { duration_seconds: Number(e.target.value) || null } })}
                />
              </td>
              <td>
                <select
                  defaultValue={ep.status}
                  onChange={(e) => updateEp.mutate({ id: ep.id, body: { status: e.target.value } })}
                >
                  <option value="draft">draft</option>
                  <option value="published">published</option>
                </select>
              </td>
              <td><EpisodeThumb episodeId={ep.id} /></td>
            </tr>
          ))}
        </tbody>
      </table>

      {showAdd ? (
        <div className="toolbar" style={{ marginTop: 8, paddingLeft: 10 }}>
          <input placeholder="Episode title" value={title} onChange={(e) => setTitle(e.target.value)} style={{ maxWidth: 220 }} />
          <input placeholder="lang (en, hi…)" value={lang} onChange={(e) => setLang(e.target.value)} style={{ maxWidth: 100 }} />
          <button className="btn btn-primary" onClick={() => { onAddEpisode(title, lang); setTitle(""); setShowAdd(false); }}>Add</button>
          <button className="btn" onClick={() => setShowAdd(false)}>Cancel</button>
        </div>
      ) : (
        <button className="btn" style={{ marginTop: 8, marginLeft: 10 }} onClick={() => setShowAdd(true)}>+ Add episode</button>
      )}
    </div>
  );
}

function EpisodeThumb({ episodeId }: { episodeId: string }) {
  const [open, setOpen] = useState(false);
  return open ? (
    <ArtworkUploadSlot kind="thumbnail" episodeId={episodeId} onUploaded={() => setOpen(false)} />
  ) : (
    <button className="btn" onClick={() => setOpen(true)}>Upload</button>
  );
}
