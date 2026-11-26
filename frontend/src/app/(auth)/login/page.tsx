import { SignInScreen } from "@/components/SignInScreen"
import { safeNextPath } from "@/lib/navigation"

type LoginPageProps = {
  searchParams: Promise<{ next?: string | string[] }>
}

// The one sign-in route for members and staff. Protected pages send visitors here
// with ?next=<path> so they return to where they started.
export default async function LoginPage({ searchParams }: LoginPageProps) {
  const { next } = await searchParams
  return <SignInScreen title="Sign in" redirectTo={safeNextPath(next)} />
}
