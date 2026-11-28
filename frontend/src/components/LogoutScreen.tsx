"use client"

import Image from "next/image"
import { useEffect, useState } from "react"
import { apiFetch, csrfHeader, ensureCsrfCookie } from "@/lib/api"

// Figma: "ILMDAS · Logout" (node 80:37)
export function LogoutScreen() {
  const [signedOut, setSignedOut] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function signOut() {
      try {
        const csrfToken = await ensureCsrfCookie()
        // A 401/403 means there was no session left to end, which is still "signed out".
        await apiFetch("/api/v1/auth/logout/", { method: "POST", headers: csrfHeader(csrfToken) })
      } catch {
        // Network failure: the server session may survive, but we still show the page.
      }
      if (!cancelled) {
        setSignedOut(true)
      }
    }
    void signOut()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="logout-screen">
      <div className="logout-card">
        <Image
          className="logout-logo"
          src="/brand/iqqo-logo.png"
          alt="IQQO logo"
          width={144}
          height={144}
          priority
        />

        {signedOut ? (
          <>
            <div className="logout-status">
              <Image src="/brand/check.svg" alt="" width={32} height={32} />
            </div>
            <div className="logout-message" role="status">
              <h1>You have signed out</h1>
              <p>
                Your session has ended on this device. Your reading history and reservations are
                saved to your account.
              </p>
            </div>
            <div className="logout-actions">
              <a className="button-primary" href="/login">
                Sign in again
              </a>
              <a className="button-secondary" href="/opac">
                Go to E-Books
              </a>
            </div>
            <p className="logout-note">
              Signing out on a shared computer? Close this browser window to be safe.
            </p>
          </>
        ) : (
          <p className="logout-message" role="status">
            Signing you out…
          </p>
        )}
      </div>
    </main>
  )
}
