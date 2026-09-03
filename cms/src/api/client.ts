// Uses Vite env vars. API_BASE and API_KEY come from .env in dev; in the
// docker-compose setup these are injected at build/runtime via VITE_* vars.
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8088";

// NOTE: for a real internal CMS this key would come from a login flow /
// token exchange, not a static env var. Kept simple here per the
// challenge's scope -- see README Part E.
function apiKey(): string {
  return localStorage.getItem("peblo_api_key") || import.meta.env.VITE_ADMIN_API_KEY || "";
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      "X-API-Key": apiKey(),
      ...(options.headers || {}),
    },
  });

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    if (res.status === 401) throw new ApiError(401, "Missing or invalid API key. Check your key in Settings.");
    if (res.status === 403) throw new ApiError(403, "You don't have permission to do that (admin required).");
    throw new ApiError(res.status, data.detail || `Request failed (${res.status})`);
  }
  return data as T;
}

export const api = {
  setApiKey(key: string) {
    localStorage.setItem("peblo_api_key", key);
  },
  getApiKey(): string {
    return apiKey();
  },

  listShows: (params: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as [string, string][]
    ).toString();
    return request<any>(`/admin/shows?${qs}`);
  },
  getShow: (id: string) => request<any>(`/admin/shows/${id}`),
  createShow: (body: any) => request<any>(`/admin/shows`, { method: "POST", body: JSON.stringify(body) }),
  updateShow: (id: string, body: any) => request<any>(`/admin/shows/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteShow: (id: string) => request<void>(`/admin/shows/${id}`, { method: "DELETE" }),

  createSeason: (body: any) => request<any>(`/admin/seasons`, { method: "POST", body: JSON.stringify(body) }),
  createEpisode: (body: any) => request<any>(`/admin/episodes`, { method: "POST", body: JSON.stringify(body) }),
  updateEpisode: (id: string, body: any) => request<any>(`/admin/episodes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteEpisode: (id: string) => request<void>(`/admin/episodes/${id}`, { method: "DELETE" }),

  uploadArtwork: (form: FormData) => request<any>(`/admin/artwork`, { method: "POST", body: form }),

  getValidationReport: () => request<any>(`/admin/validation-report`),
  publish: () => request<any>(`/admin/catalog/publish`, { method: "POST" }),
  listRuns: () => request<any[]>(`/admin/catalog/runs`),
};
