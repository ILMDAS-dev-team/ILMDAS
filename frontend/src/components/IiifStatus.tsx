"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"

export function IiifStatus() {
  const [message, setMessage] = useState("Checking IIIF configuration")

  useEffect(() => {
    let cancelled = false
    apiFetch("/api/v1/iiif/status/")
      .then(async ({ response }) => {
        if (cancelled) return
        if (!response.ok) {
          setMessage("IIIF endpoint is not configured")
          return
        }
        const body = (await response.json()) as { message?: string; status?: string }
        if (body.status === "not_configured" || !body.message) {
          setMessage("IIIF endpoint is not configured")
          return
        }
        setMessage(body.message)
      })
      .catch(() => {
        if (!cancelled) setMessage("IIIF endpoint is not configured")
      })
    return () => {
      cancelled = true
    }
  }, [])

  return <p role="status">{message}</p>
}
