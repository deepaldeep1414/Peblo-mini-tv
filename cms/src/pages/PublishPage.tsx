import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";

export default function PublishPage() {
  const qc = useQueryClient();

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["validation-report"],
    queryFn: api.getValidationReport,
  });

  const { data: runs } = useQuery({ queryKey: ["runs"], queryFn: api.listRuns });

  const publishMutation = useMutation({
    mutationFn: api.publish,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["runs"] });
      qc.invalidateQueries({ queryKey: ["validation-report"] });
    },
  });

  if (error) {
    const apiErr = error as ApiError;
    if (apiErr.status === 403) {
      return (
        <div>
          <h2>Publish</h2>
          <div className="error-banner">
            Publishing requires the admin role. Switch to an admin API key on the Settings page.
          </div>
        </div>
      );
    }
    return <div className="error-banner">{apiErr.message}</div>;
  }

  const blockingCount = report?.blocking_issue_count ?? 0;

  return (
    <div>
      <h2>Publish</h2>

      <div className="card">
        <div className="toolbar">
          <div style={{ marginRight: "auto" }}>
            <strong>{blockingCount}</strong> blocking issue{blockingCount === 1 ? "" : "s"}
            {report && <span style={{ color: "#888", marginLeft: 8, fontSize: 13 }}>
              as of {new Date(report.generated_at).toLocaleTimeString()}
            </span>}
          </div>
          <button
            className="btn btn-primary"
            disabled={blockingCount > 0 || publishMutation.isPending}
            onClick={() => publishMutation.mutate()}
            title={blockingCount > 0 ? "Fix the issues below before publishing" : "Publish the catalogue now"}
          >
            {publishMutation.isPending ? "Publishing…" : "Publish catalogue"}
          </button>
        </div>
        {publishMutation.isError && (
          <div className="error-banner">
            {(publishMutation.error as ApiError).message}
          </div>
        )}
        {publishMutation.isSuccess && (
          <div style={{ color: "#1e7d43", fontSize: 14 }}>
            Published {publishMutation.data.shows_count} shows / {publishMutation.data.episodes_count} episodes successfully.
          </div>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Validation report</h3>
        {isLoading && <div className="empty-state">Checking for issues…</div>}
        {!isLoading && blockingCount === 0 && (
          <div className="empty-state">Nothing is blocking publish. You're clear to go.</div>
        )}
        {!isLoading && Object.entries(report?.issues_by_show || {}).map(([showId, issues]: [string, any]) => (
          <div key={showId} style={{ marginBottom: 12 }}>
            {issues.map((issue: any, i: number) => (
              <div className="issue-row" key={i}>{issue.message}</div>
            ))}
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Run history</h3>
        {!runs || runs.length === 0 ? (
          <div className="empty-state">No publish runs yet.</div>
        ) : (
          <table>
            <thead><tr><th>Started</th><th>By</th><th>Outcome</th><th>Shows</th><th>Episodes</th></tr></thead>
            <tbody>
              {runs.map((run: any) => (
                <tr key={run.id}>
                  <td>{new Date(run.started_at).toLocaleString()}</td>
                  <td>{run.triggered_by}</td>
                  <td>
                    <span className={`badge ${run.outcome === "success" ? "badge-published" : "badge-draft"}`}>
                      {run.outcome}
                    </span>
                  </td>
                  <td>{run.shows_count}</td>
                  <td>{run.episodes_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
