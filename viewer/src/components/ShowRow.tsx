import { CatalogueShow } from "../api/client";
import PosterCard from "./PosterCard";

export default function ShowRow({ title, shows }: { title: string; shows: CatalogueShow[] }) {
  if (shows.length === 0) return null;
  return (
    <div className="row">
      <h2>{title}</h2>
      <div className="row-track">
        {shows.map((show) => (
          <PosterCard key={show.id} id={show.id} title={show.title} posterKey={show.poster_key} />
        ))}
      </div>
    </div>
  );
}
