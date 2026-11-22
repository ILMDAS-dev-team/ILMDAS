import { redirect } from "next/navigation"
import { verifyStaffSession } from "@/lib/auth"

export default async function StaffSectionPage({
  params,
}: {
  params: Promise<{ section: string }>
}) {
  const isAuthenticated = await verifyStaffSession()
  if (!isAuthenticated) {
    redirect("/sign-in")
  }

  return (
    <section>
      <StaffSection params={params} />
    </section>
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
