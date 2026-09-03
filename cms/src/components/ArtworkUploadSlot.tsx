import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";

const SPECS: Record<string, string> = {
  poster: "2:3 ratio, ~600×900px",
  banner: "16:9 ratio, ~1280×720px",
  thumbnail: "16:9 ratio, ~640×360px",
};

export default function ArtworkUploadSlot({
  kind, showId, episodeId, existing, onUploaded,
}: {
  kind: "poster" | "banner" | "thumbnail";
  showId?: string;
  episodeId?: string;
  existing?: { url: string } | null;
  onUploaded?: () => void;
}) {
  const [preview, setPreview] = useState<string | null>(existing?.url || null);
  const [error, setError] = useState<string | null>(null);
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("kind", kind);
      if (showId) form.append("show_id", showId);
      if (episodeId) form.append("episode_id", episodeId);
      form.append("file", file);
      return api.uploadArtwork(form);
    },
    onSuccess: (data) => {
      setError(null);
      setPreview(data.url);
      onUploaded?.();
      qc.invalidateQueries({ queryKey: ["show"] });
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    },
  });

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const localUrl = URL.createObjectURL(file);
    setPreview(localUrl);
    mutation.mutate(file);
  }

  return (
    <div className="upload-slot">
      <div style={{ fontWeight: 600, marginBottom: 6, textTransform: "capitalize" }}>{kind}</div>
      {preview && <img src={preview} alt={`${kind} preview`} />}
      <div className="spec-hint">Required: {SPECS[kind]} · max 200 KB</div>
      <div style={{ marginTop: 8 }}>
        <input type="file" accept="image/*" onChange={handleFile} disabled={mutation.isPending} />
      </div>
      {mutation.isPending && <div className="spec-hint">Uploading…</div>}
      {error && <div className="error-banner" style={{ marginTop: 8, marginBottom: 0 }}>{error}</div>}
    </div>
  );
}
