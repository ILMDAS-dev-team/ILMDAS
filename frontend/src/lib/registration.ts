/**
 * Account registration API (ILMDAS-551, ILMDAS-552).
 *
 * Self-registration and staff invites both create a pending account. The emailed link
 * carries a `uid` and `token`, which these calls post back to activate the account.
 */

import { sendJson } from "@/lib/apiErrors"

export type RegistrationInput = {
  username: string
  email: string
  first_name: string
  last_name: string
  password: string
  accept_terms: boolean
}

export type StaffAccountInput = {
  username: string
  email: string
  first_name: string
  last_name: string
  roles: string[]
}

export type StaffAccount = {
  id: number
  username: string
  email: string
  status: string
  roles: { code: string; name: string }[]
}

type DetailResponse = { detail: string }

export function registerAccount(input: RegistrationInput): Promise<DetailResponse> {
  return sendJson("/api/v1/auth/register/", input, "Your account could not be created.")
}

export function verifyEmail(uid: string, token: string): Promise<DetailResponse> {
  return sendJson("/api/v1/auth/verify-email/", { uid, token }, "This link could not be used.")
}

export function resendVerification(email: string): Promise<DetailResponse> {
  return sendJson("/api/v1/auth/verify-email/resend/", { email }, "No new link could be sent.")
}

export function acceptInvite(
  uid: string,
  token: string,
  password: string
): Promise<DetailResponse> {
  return sendJson(
    "/api/v1/auth/invite/accept/",
    { uid, token, password },
    "Your password could not be set."
  )
}

export function createStaffAccount(input: StaffAccountInput): Promise<StaffAccount> {
  return sendJson("/api/v1/users/staff/", input, "The staff account could not be created.")
}
