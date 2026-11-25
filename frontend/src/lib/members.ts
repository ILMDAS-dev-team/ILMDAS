// Server-only helpers for staff member records. Do not import from a client component.

const DEFAULT_API_URL = "http://localhost:8010"
const MEMBER_ID_PATTERN = /^[1-9]\d*$/

export interface MemberCategory {
  id: number
  code: string
  name: string
  isActive: boolean
}

export interface MemberMembership {
  id: number
  category: MemberCategory
  joinedAt: string
}

export interface BorrowingEligibility {
  eligible: boolean
  reason: string | null
  message: string
}

export interface MemberRecord {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  status: string
  role: string
  membership: MemberMembership | null
  borrowingEligibility: BorrowingEligibility
}

export type MemberLookupResult =
  | { status: "ok"; member: MemberRecord }
  | { status: "unauthenticated" }
  | { status: "forbidden" }
  | { status: "not_found" }
  | { status: "error" }

export function normalizeMemberId(value: string | undefined): string | null {
  const trimmed = value?.trim()
  if (!trimmed || !MEMBER_ID_PATTERN.test(trimmed)) {
    return null
  }
  return trimmed
}

function apiRoot(): string {
  const configured =
    process.env.ILMDAS_API_URL || process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL
  return configured.replace(/\/$/, "")
}

export async function fetchMemberRecord(
  memberId: string,
  sessionId: string,
  baseUrl = apiRoot()
): Promise<MemberLookupResult> {
  // Re-validate here as well so an invalid ID can never become part of the URL.
  if (!MEMBER_ID_PATTERN.test(memberId)) {
    return { status: "error" }
  }

  try {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/v1/members/${memberId}/`, {
      headers: {
        Accept: "application/json",
        Cookie: `sessionid=${sessionId}`,
      },
      cache: "no-store",
    })

    if (response.status === 401) return { status: "unauthenticated" }
    if (response.status === 403) return { status: "forbidden" }
    if (response.status === 404) return { status: "not_found" }
    if (!response.ok) return { status: "error" }

    return { status: "ok", member: (await response.json()) as MemberRecord }
  } catch {
    return { status: "error" }
  }
}
