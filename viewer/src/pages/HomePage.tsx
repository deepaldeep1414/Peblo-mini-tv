import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, artworkUrl } from "../api/client";
import ShowRow from "../components/ShowRow";

export default function HomePage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["catalog"], queryFn: api.getCatalog });
  const [heroFailed, setHeroFailed] = useState(false);

  if (isLoading) return <div className="empty-state">Loading Peblo TV…</div>;

  if (error) {
    return (
      <div className="empty-state">
        Nothing's been published yet. Check back soon!
      </div>
    );
  }

  const allShows = data!.sections.flatMap((s) => s.shows);
  if (allShows.length === 0) {
    return <div className="empty-state">No shows are published yet. Check back soon!</div>;
  }

  const featured = allShows[0];
  const bannerUrl = artworkUrl(featured.banner_key);

  return (
    <>
      <Link to={`/shows/${featured.id}`}>
        <div className="hero">
          {bannerUrl && !heroFailed ? (
            <img src={bannerUrl} alt={featured.title} onError={() => setHeroFailed(true)} />
          ) : null}
          <div className="hero-fade" />
          <div className="hero-content">
            <h1>{featured.title}</h1>
            <p>{featured.synopsis}</p>
          </div>
        </div>
      </Link>

      <div className="rows">
        {data!.sections.map((section) => (
          <ShowRow key={section.section} title={section.section} shows={section.shows} />
        ))}
      </div>
    </>
  );
}
