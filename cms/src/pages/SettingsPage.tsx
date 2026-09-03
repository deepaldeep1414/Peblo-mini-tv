import { useState } from "react";
import { api } from "../api/client";

export default function SettingsPage() {
  const [key, setKey] = useState(api.getApiKey());
  const [saved, setSaved] = useState(false);

  return (
    <div>
      <h2>Settings</h2>
      <div className="card" style={{ maxWidth: 480 }}>
        <div className="field">
          <label>API Key</label>
          <input
            value={key}
            onChange={(e) => { setKey(e.target.value); setSaved(false); }}
            placeholder="editor-key-change-me or admin-key-change-me"
          />
          <p className="spec-hint">
            Demo auth: paste the editor or admin key from your backend's .env.
            Admin unlocks Publish; editor can manage shows/episodes only.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => { api.setApiKey(key); setSaved(true); }}>
          Save
        </button>
        {saved && <span style={{ marginLeft: 10, color: "#1e7d43" }}>Saved.</span>}
      </div>
    </div>
  );
}
