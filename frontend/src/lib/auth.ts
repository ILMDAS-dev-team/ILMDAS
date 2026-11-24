import { cookies } from "next/headers"

export async function verifyStaffSession(): Promise<boolean> {
  const cookieStore = await cookies()
  const sessionId = cookieStore.get("sessionid")?.value
  return Boolean(sessionId)
}
