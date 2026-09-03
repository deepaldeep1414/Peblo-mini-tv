import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api, artworkUrl, CatalogueEpisode } from "../api/client";

export default function ShowDetailPage() {
  const { showId } = useParams();
  const { data, isLoading, error } = useQuery({ queryKey: ["catalog"], queryFn: api.getCatalog });

  if (isLoading) return <div className="empty-state">Loading…</div>;
  if (error) return <div className="empty-state">Couldn't load this show right now.</div>;

  const show = data!.sections.flatMap((s) => s.shows).find((s) => s.id === showId);
  if (!show) return <div className="empty-state">This show isn't available.</div>;

  const bannerUrl = artworkUrl(show.banner_key);

  return (
    <div>
      <Link to="/" className="back-link">← Back</Link>
      <div className="detail-header">
        {bannerUrl && <img src={bannerUrl} alt={show.title} />}
      </div>
      <div className="detail-body">
        <h1>{show.title}</h1>
        <p className="category">{show.category}</p>
        <p>{show.synopsis}</p>

        {show.trailers?.length > 0 && (
          <div className="season-block">
            <h3>Trailers</h3>
            {show.trailers.map((ep, i) => <EpisodeRow key={i} ep={ep} />)}
          </div>
        )}

        {show.seasons
          .sort((a, b) => a.season_number - b.season_number)
          .map((season) => (
            <div className="season-block" key={season.season_number}>
              <h3>Season {season.season_number}</h3>
              {season.episodes.map((ep, i) => <EpisodeRow key={i} ep={ep} />)}
            </div>
          ))}
      </div>
    </div>
  );
}

function EpisodeRow({ ep }: { ep: CatalogueEpisode }) {
  const [failed, setFailed] = useState(false);
  const thumbUrl = artworkUrl(ep.thumbnail_key);

  return (
    <div className="episode-row">
      {thumbUrl && !failed ? (
        <img src={thumbUrl} className="episode-thumb" onError={() => setFailed(true)} alt={ep.title} />
      ) : (
        <div className="episode-thumb-fallback" />
      )}
      <div>
        <div style={{ fontSize: 14 }}>
          E{ep.episode_number} · {ep.title}
          {ep.duration_seconds ? ` · ${Math.round(ep.duration_seconds / 60)} min` : ""}
        </div>
        {ep.languages && ep.languages.length > 0 && (
          <div style={{ marginTop: 4 }}>
            {ep.languages.map((l) => <span key={l.language} className="lang-pill">{l.language}</span>)}
          </div>
        )}
      </div>
    </div>
  );
}
