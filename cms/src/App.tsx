import { NavLink, Route, Routes } from "react-router-dom";
import ShowListPage from "./pages/ShowListPage";
import ShowEditPage from "./pages/ShowEditPage";
import PublishPage from "./pages/PublishPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Peblo TV · CMS</h1>
        <nav>
          <NavLink to="/" end>Shows</NavLink>
          <NavLink to="/publish">Publish</NavLink>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<ShowListPage />} />
          <Route path="/shows/new" element={<ShowEditPage />} />
          <Route path="/shows/:showId" element={<ShowEditPage />} />
          <Route path="/publish" element={<PublishPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
