import { useState } from "react";
import { Link } from "react-router-dom";
import { artworkUrl } from "../api/client";

export default function PosterCard({ id, title, posterKey }: { id: string; title: string; posterKey: string | null }) {
  const [failed, setFailed] = useState(false);
  const url = artworkUrl(posterKey);

  return (
    <Link to={`/shows/${id}`} className="poster-card">
      {url && !failed ? (
        <img src={url} alt={title} loading="lazy" onError={() => setFailed(true)} />
      ) : (
        <div className="poster-fallback">{title}</div>
      )}
      <div className="title">{title}</div>
    </Link>
  );
}
