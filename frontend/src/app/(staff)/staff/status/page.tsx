import { redirect } from "next/navigation"
import { IiifStatus } from "@/components/IiifStatus"
import { verifyStaffSession } from "@/lib/auth"

export default async function StaffStatusPage() {
  const isAuthenticated = await verifyStaffSession()
  if (!isAuthenticated) {
    redirect("/sign-in")
  }

  return (
    <section>
      <h1>Image service</h1>
      <IiifStatus />
    </section>
  )
}
