import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import {
  getBusinessDetailApiV1BusinessesBusinessIdGetOptions,
  getBusinessDetailApiV1BusinessesBusinessIdGetQueryKey,
  riskHistoryApiV1BusinessesBusinessIdRiskHistoryGetOptions,
  riskHistoryApiV1BusinessesBusinessIdRiskHistoryGetQueryKey,
  triggerEvaluateApiV1BusinessesBusinessIdEvaluatePostMutation,
} from "../api/generated/@tanstack/react-query.gen";
import { RiskBadge } from "../components/RiskBadge";
import { formatApiError } from "../lib/apiError";

export const Route = createFileRoute("/businesses/$businessId")({
  component: BusinessDetailPage,
});

const HISTORY_PAGE_SIZE = 50;

function BusinessDetailPage() {
  const { businessId } = Route.useParams();
  const queryClient = useQueryClient();
  const [historySkip, setHistorySkip] = useState(0);

  const detailQuery = useQuery({
    ...getBusinessDetailApiV1BusinessesBusinessIdGetOptions({
      path: { business_id: businessId },
    }),
    refetchInterval: (query) =>
      query.state.data?.pending_evaluation ? 2000 : false,
  });

  const historyQuery = useQuery({
    ...riskHistoryApiV1BusinessesBusinessIdRiskHistoryGetOptions({
      path: { business_id: businessId },
      query: { skip: historySkip, limit: HISTORY_PAGE_SIZE },
    }),
    refetchInterval: () => (detailQuery.data?.pending_evaluation ? 2000 : false),
  });

  const evaluateMutation = useMutation({
    ...triggerEvaluateApiV1BusinessesBusinessIdEvaluatePostMutation(),
    onSuccess: async () => {
      setHistorySkip(0);
      await queryClient.invalidateQueries({
        queryKey: getBusinessDetailApiV1BusinessesBusinessIdGetQueryKey({
          path: { business_id: businessId },
        }),
      });
      await queryClient.invalidateQueries({
        queryKey: riskHistoryApiV1BusinessesBusinessIdRiskHistoryGetQueryKey({
          path: { business_id: businessId },
        }),
      });
    },
  });

  const business = detailQuery.data;
  const historyTotal = historyQuery.data?.total ?? 0;
  const historyPageEnd = Math.min(historySkip + HISTORY_PAGE_SIZE, historyTotal);

  return (
    <div className="space-y-8">
      <p>
        <Link to="/" className="text-sm text-blue-600 hover:underline">
          ← Back to list
        </Link>
      </p>

      {detailQuery.isLoading && (
        <p className="text-sm text-slate-500">Loading business…</p>
      )}
      {detailQuery.isError && (
        <p className="text-sm text-rose-600">
          {formatApiError(detailQuery.error, "Business not found or failed to load.")}
        </p>
      )}

      {business && (
        <>
          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-semibold">{business.name}</h1>
                <p className="mt-1 text-sm text-slate-600">
                  {business.industry ?? "No industry"}
                </p>
                <p className="mt-2 text-xs text-slate-400">
                  Created {new Date(business.created_at).toLocaleString()}
                </p>
              </div>
              <button
                type="button"
                disabled={evaluateMutation.isPending || !!business.pending_evaluation}
                onClick={() =>
                  evaluateMutation.mutate({
                    path: { business_id: businessId },
                  })
                }
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {evaluateMutation.isPending
                  ? "Triggering…"
                  : business.pending_evaluation
                    ? "Evaluation in progress"
                    : "Trigger risk evaluation"}
              </button>
            </div>

            {evaluateMutation.isError && (
              <p className="mt-3 text-sm text-rose-600">
                {formatApiError(
                  evaluateMutation.error,
                  "Failed to trigger evaluation.",
                )}
              </p>
            )}
            {evaluateMutation.isSuccess && (
              <p className="mt-3 text-sm text-emerald-700">
                Evaluation queued (status: {evaluateMutation.data.status}).
              </p>
            )}

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-md bg-slate-50 p-4">
                <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Latest completed risk
                </h2>
                {business.latest_completed_risk ? (
                  <div className="mt-2 space-y-1 text-sm">
                    <p>
                      Score:{" "}
                      <span className="font-medium">
                        {business.latest_completed_risk.score}
                      </span>
                    </p>
                    <p className="flex items-center gap-2">
                      Level:{" "}
                      <RiskBadge level={business.latest_completed_risk.risk_level} />
                    </p>
                    <p className="text-slate-500">
                      {new Date(
                        business.latest_completed_risk.completed_at,
                      ).toLocaleString()}
                    </p>
                  </div>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">No completed evaluation yet.</p>
                )}
              </div>
              <div className="rounded-md bg-slate-50 p-4">
                <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Active evaluation
                </h2>
                {business.pending_evaluation ? (
                  <p className="mt-2 text-sm text-amber-700">
                    In progress (requested{" "}
                    {new Date(
                      business.pending_evaluation.requested_at,
                    ).toLocaleString()}
                    ). Polling every 2s…
                  </p>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">None</p>
                )}
              </div>
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-4 py-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Risk history
                {historyQuery.data != null && (
                  <span className="ml-2 font-normal normal-case text-slate-400">
                    ({historyQuery.data.total} total)
                  </span>
                )}
              </h2>
              {historyTotal > HISTORY_PAGE_SIZE && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <button
                    type="button"
                    disabled={historySkip === 0 || historyQuery.isFetching}
                    onClick={() =>
                      setHistorySkip((s) => Math.max(0, s - HISTORY_PAGE_SIZE))
                    }
                    className="rounded border border-slate-300 px-2 py-1 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span>
                    {historyTotal === 0
                      ? "0"
                      : `${historySkip + 1}–${historyPageEnd}`}{" "}
                    of {historyTotal}
                  </span>
                  <button
                    type="button"
                    disabled={
                      historySkip + HISTORY_PAGE_SIZE >= historyTotal ||
                      historyQuery.isFetching
                    }
                    onClick={() => setHistorySkip((s) => s + HISTORY_PAGE_SIZE)}
                    className="rounded border border-slate-300 px-2 py-1 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
            {historyQuery.isLoading && (
              <p className="px-4 py-6 text-sm text-slate-500">Loading history…</p>
            )}
            {historyQuery.isError && (
              <p className="px-4 py-6 text-sm text-rose-600">
                {formatApiError(historyQuery.error, "Failed to load history.")}
              </p>
            )}
            {historyQuery.data && historyQuery.data.items.length === 0 && (
              <p className="px-4 py-6 text-sm text-slate-500">No evaluations yet.</p>
            )}
            {historyQuery.data && historyQuery.data.items.length > 0 && (
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-2 font-medium">Status</th>
                    <th className="px-4 py-2 font-medium">Score</th>
                    <th className="px-4 py-2 font-medium">Level</th>
                    <th className="px-4 py-2 font-medium">Requested</th>
                    <th className="px-4 py-2 font-medium">Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {historyQuery.data.items.map((row) => (
                    <tr key={row.id} className="border-t border-slate-100">
                      <td className="px-4 py-2 capitalize">{row.status}</td>
                      <td className="px-4 py-2">{row.score ?? "—"}</td>
                      <td className="px-4 py-2">
                        <RiskBadge level={row.risk_level} />
                      </td>
                      <td className="px-4 py-2 text-slate-600">
                        {new Date(row.requested_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-2 text-slate-600">
                        {row.completed_at
                          ? new Date(row.completed_at).toLocaleString()
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  );
}
