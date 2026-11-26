"use client"

import { RequireRole } from "@/components/RequireRole"

export default function StaffHomePage() {
  return (
    <RequireRole requireStaff>
      <section>
        <h1>Staff workspace</h1>
        <p>Module screens are added in their own sprints. This shell only reserves their places.</p>
      </section>
    </RequireRole>
  )
}
