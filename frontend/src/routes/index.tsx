import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import {
  createBusinessRouteApiV1BusinessesPostMutation,
  listBusinessesRouteApiV1BusinessesGetOptions,
  listBusinessesRouteApiV1BusinessesGetQueryKey,
} from "../api/generated/@tanstack/react-query.gen";
import type { RiskLevel } from "../api/generated/types.gen";
import { formatApiError } from "../lib/apiError";

export const Route = createFileRoute("/")({
  component: BusinessesPage,
});

const PAGE_SIZE = 50;

function BusinessesPage() {
  const queryClient = useQueryClient();
  const [nameFilter, setNameFilter] = useState("");
  const [debouncedName, setDebouncedName] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "">("");
  const [skip, setSkip] = useState(0);
  const [newName, setNewName] = useState("");
  const [newIndustry, setNewIndustry] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedName(nameFilter), 300);
    return () => window.clearTimeout(timer);
  }, [nameFilter]);

  useEffect(() => {
    setSkip(0);
  }, [debouncedName, riskFilter]);

  const listQuery = useQuery(
    listBusinessesRouteApiV1BusinessesGetOptions({
      query: {
        name: debouncedName.trim() || undefined,
        risk_level: riskFilter || undefined,
        skip,
        limit: PAGE_SIZE,
      },
    }),
  );

  const createMutation = useMutation({
    ...createBusinessRouteApiV1BusinessesPostMutation(),
    onSuccess: async () => {
      setNewName("");
      setNewIndustry("");
      await queryClient.invalidateQueries({
        queryKey: listBusinessesRouteApiV1BusinessesGetQueryKey(),
      });
    },
  });

  const total = listQuery.data?.total ?? 0;
  const pageEnd = Math.min(skip + PAGE_SIZE, total);

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">Businesses</h1>
        <p className="mt-1 text-sm text-slate-600">
          List, filter by risk factor, and create businesses.
        </p>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Filters
        </h2>
        <div className="flex flex-wrap gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Name
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              value={nameFilter}
              onChange={(e) => setNameFilter(e.target.value)}
              placeholder="substring"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Risk factor
            <select
              className="rounded-md border border-slate-300 px-3 py-2"
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value as RiskLevel | "")}
            >
              <option value="">Any</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Create business
        </h2>
        <form
          className="flex flex-wrap items-end gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate({
              body: {
                name: newName.trim(),
                industry: newIndustry.trim() || null,
              },
            });
          }}
        >
          <label className="flex flex-col gap-1 text-sm">
            Name *
            <input
              required
              className="rounded-md border border-slate-300 px-3 py-2"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Industry
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              value={newIndustry}
              onChange={(e) => setNewIndustry(e.target.value)}
            />
          </label>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createMutation.isPending ? "Creating…" : "Create"}
          </button>
        </form>
        {createMutation.isError && (
          <p className="mt-2 text-sm text-rose-600">
            {formatApiError(createMutation.error, "Failed to create business.")}
          </p>
        )}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Results
            {listQuery.data != null && (
              <span className="ml-2 font-normal normal-case text-slate-400">
                ({listQuery.data.total} total)
              </span>
            )}
          </h2>
          {total > PAGE_SIZE && (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <button
                type="button"
                disabled={skip === 0 || listQuery.isFetching}
                onClick={() => setSkip((s) => Math.max(0, s - PAGE_SIZE))}
                className="rounded border border-slate-300 px-2 py-1 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <span>
                {total === 0 ? "0" : `${skip + 1}–${pageEnd}`} of {total}
              </span>
              <button
                type="button"
                disabled={skip + PAGE_SIZE >= total || listQuery.isFetching}
                onClick={() => setSkip((s) => s + PAGE_SIZE)}
                className="rounded border border-slate-300 px-2 py-1 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
        {listQuery.isLoading && (
          <p className="px-4 py-6 text-sm text-slate-500">Loading…</p>
        )}
        {listQuery.isError && (
          <p className="px-4 py-6 text-sm text-rose-600">
            {formatApiError(listQuery.error, "Failed to load businesses.")}
          </p>
        )}
        {listQuery.data && listQuery.data.items.length === 0 && (
          <p className="px-4 py-6 text-sm text-slate-500">No businesses found.</p>
        )}
        {listQuery.data && listQuery.data.items.length > 0 && (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2 font-medium">Name</th>
                <th className="px-4 py-2 font-medium">Industry</th>
                <th className="px-4 py-2 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {listQuery.data.items.map((business) => (
                <tr key={business.id} className="border-t border-slate-100">
                  <td className="px-4 py-2">
                    <Link
                      to="/businesses/$businessId"
                      params={{ businessId: business.id }}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {business.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {business.industry ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {new Date(business.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
