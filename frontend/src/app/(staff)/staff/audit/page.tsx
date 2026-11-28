"use client"

import { FormEvent, useCallback, useEffect, useState } from "react"
import { RequireRole } from "@/components/RequireRole"
import { fetchAuditEvents, type AuditFilters, type AuditPage } from "@/lib/audit"
import { ROLE_SYSTEM_ADMINISTRATOR } from "@/lib/roles"

// Read-only audit review (ILMDAS-31). There are deliberately no edit or delete controls.
function AuditLog() {
  const [draft, setDraft] = useState<AuditFilters>({})
  const [filters, setFilters] = useState<AuditFilters>({ page: 1 })
  const [data, setData] = useState<AuditPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (current: AuditFilters) => {
    setLoading(true)
    setError(null)
    try {
      setData(await fetchAuditEvents(current))
    } catch {
      setError("Could not load audit events.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load(filters)
  }, [filters, load])

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFilters({ ...draft, page: 1 })
  }

  const page = filters.page ?? 1

  return (
    <section>
      <h1>Audit log</h1>
      <form onSubmit={onSubmit} aria-label="Filter audit events">
        <label>
          Actor
          <input
            value={draft.actor ?? ""}
            onChange={(e) => setDraft({ ...draft, actor: e.target.value })}
          />
        </label>
        <label>
          Action
          <input
            placeholder="e.g. auth. or role.assigned"
            value={draft.action ?? ""}
            onChange={(e) => setDraft({ ...draft, action: e.target.value })}
          />
        </label>
        <label>
          From
          <input
            type="date"
            value={draft.dateFrom ?? ""}
            onChange={(e) => setDraft({ ...draft, dateFrom: e.target.value })}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={draft.dateTo ?? ""}
            onChange={(e) => setDraft({ ...draft, dateTo: e.target.value })}
          />
        </label>
        <button type="submit">Apply filters</button>
      </form>

      {error ? <p role="alert">{error}</p> : null}
      {loading ? <p>Loading...</p> : null}

      {data && !loading ? (
        <>
          <p>{data.count} events</p>
          <table>
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">Actor</th>
                <th scope="col">Action</th>
                <th scope="col">Target</th>
                <th scope="col">Outcome</th>
                <th scope="col">Correlation id</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((event) => (
                <tr key={event.id}>
                  <td>{new Date(event.timestamp).toLocaleString()}</td>
                  <td>{event.actor_username || "system"}</td>
                  <td>{event.action}</td>
                  <td>
                    {event.object_type}
                    {event.object_id ? `:${event.object_id}` : ""}
                  </td>
                  <td>{event.outcome}</td>
                  <td>{event.correlation_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <nav aria-label="Audit pages">
            <button
              type="button"
              disabled={!data.previous}
              onClick={() => setFilters({ ...filters, page: page - 1 })}
            >
              Previous
            </button>
            <span> Page {page} </span>
            <button
              type="button"
              disabled={!data.next}
              onClick={() => setFilters({ ...filters, page: page + 1 })}
            >
              Next
            </button>
          </nav>
        </>
      ) : null}
    </section>
  )
}

export default function AuditPageRoute() {
  return (
    <RequireRole role={ROLE_SYSTEM_ADMINISTRATOR}>
      <AuditLog />
    </RequireRole>
  )
}
