import { redirect } from "next/navigation"
import { verifyStaffSession } from "@/lib/auth"

export default async function StaffHomePage() {
  const isAuthenticated = await verifyStaffSession()
  if (!isAuthenticated) {
    redirect("/sign-in")
  }

  return (
    <section>
      <h1>Staff workspace</h1>
      <p>Module screens are added in their own sprints. This shell only reserves their places.</p>
    </section>
  )
}
