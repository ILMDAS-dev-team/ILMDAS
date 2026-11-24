import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith("/staff")) {
    const sessionId = request.cookies.get("sessionid")?.value
    if (!sessionId) {
      const signInUrl = new URL("/sign-in", request.url)
      return NextResponse.redirect(signInUrl)
    }
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/staff/:path*"],
}
