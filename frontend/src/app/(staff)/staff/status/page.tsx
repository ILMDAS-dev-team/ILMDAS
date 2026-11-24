"use client"

import { RequireRole } from "@/components/RequireRole"
import { IiifStatus } from "@/components/IiifStatus"

export default function StaffStatusPage() {
  return (
    <RequireRole requireStaff>
      <section>
        <h1>Image service</h1>
        <IiifStatus />
      </section>
    </RequireRole>
  )
}
