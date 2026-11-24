"use client"

import { RequireRole } from "@/components/RequireRole"

export default function StaffSectionPage({ params }: { params: Promise<{ section: string }> }) {
  return (
    <RequireRole requireStaff>
      <StaffSection params={params} />
    </RequireRole>
  )
}

async function StaffSection({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params
  const title = section.slice(0, 1).toUpperCase() + section.slice(1)
  return (
    <>
      <h1>{title}</h1>
      <p>This workspace is reserved for a later sprint.</p>
    </>
  )
}
