import { useState } from "react";
import { Link, Route, Routes, useNavigate } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import ShowDetailPage from "./pages/ShowDetailPage";

export default function App() {
  const [q, setQ] = useState("");
  const navigate = useNavigate();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    navigate(q ? `/search?q=${encodeURIComponent(q)}` : "/search");
  }

  return (
    <>
      <div className="topbar">
        <Link to="/" className="logo">PEBLO TV</Link>
        <form onSubmit={handleSubmit} style={{ display: "contents" }}>
          <input
            placeholder="Search shows and episodes…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </form>
      </div>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/shows/:showId" element={<ShowDetailPage />} />
      </Routes>
    </>
  );
}
