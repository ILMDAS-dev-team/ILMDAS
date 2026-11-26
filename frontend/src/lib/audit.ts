/**
 * Read-only audit review API (ILMDAS-31). The backend allows GET only.
 */

import { apiFetch } from "@/lib/api"

export type AuditEvent = {
  id: number
  timestamp: string
  actor_username: string
  action: string
  object_type: string
  object_id: string
  outcome: "success" | "failure" | "denied"
  correlation_id: string
  details: Record<string, unknown>
}

export type AuditFilters = {
  actor?: string
  action?: string
  dateFrom?: string
  dateTo?: string
  page?: number
}

export type AuditPage = {
  count: number
  next: string | null
  previous: string | null
  results: AuditEvent[]
}

export function auditQuery(filters: AuditFilters): string {
  const params = new URLSearchParams()
  if (filters.actor?.trim()) params.set("actor", filters.actor.trim())
  if (filters.action?.trim()) params.set("action", filters.action.trim())
  if (filters.dateFrom) params.set("date_from", filters.dateFrom)
  if (filters.dateTo) params.set("date_to", filters.dateTo)
  if (filters.page && filters.page > 1) params.set("page", String(filters.page))
  const query = params.toString()
  return query ? `?${query}` : ""
}

export async function fetchAuditEvents(filters: AuditFilters = {}): Promise<AuditPage> {
  const { response } = await apiFetch(`/api/v1/audit/events/${auditQuery(filters)}`)
  if (!response.ok) throw new Error(`Failed to load audit events: ${response.status}`)
  return (await response.json()) as AuditPage
}
