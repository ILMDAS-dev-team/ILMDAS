# Registration and membership API (ILMDAS-549)

This document covers how accounts are created and how a guest becomes a member. Jira: ILMDAS-549, subtasks ILMDAS-550 to 555. Requirements: FR-MEM-002 and FR-MEM-006.

All paths are under `/api/v1/`. Errors use the shared error format (`code`, `message`, `correlationId`, `errors`). Anonymous `POST` endpoints need the CSRF cookie and the `X-CSRFToken` header. Get the cookie from `GET auth/csrf/`.

## Roles and account status

- **Every new account gets the `guest` role.** A guest can use public discovery and their own account pages. Existing accounts kept their roles when `guest` was added.
- **Only an approved membership grants `member`.** The member role is removed again when the membership expires. Use the `apps.membership.permissions.IsMember` permission on member-only endpoints, such as borrowing.
- **Pending accounts can't sign in.** Self-registered accounts and staff invites start as `pending`. They become `active` when the email is verified or the invite is accepted.

## Staff accounts (system administrator only)

| Method and path | Body | Result |
|---|---|---|
| `POST users/staff/` | `username`, `email`, `first_name`, `last_name`, `roles` (one or more of `system_administrator`, `librarian`, `digital_archivist`, `journal_editor`, `manager`, `integration_administrator`) | `201`. A pending account with no usable password. An invite email is sent. |
| `POST auth/invite/accept/` (anonymous) | `uid`, `token` (from the invite link), `password` | `200`. The password is set and the account is active. |

`guest` and `member` can't be granted here. If the username or email is already taken, the API returns one generic error that doesn't say which one.

## Self-registration (anonymous, rate-limited)

| Method and path | Body | Result |
|---|---|---|
| `POST auth/register/` | `username`, `email`, `first_name`, `last_name` (optional), `password`, `accept_terms: true` | `201`. A pending account. A verification email is sent. |
| `POST auth/verify-email/` | `uid`, `token` (from the link) | `200`. The account is an active guest. |
| `POST auth/verify-email/resend/` | `email` | `200` with the same answer whether or not the email exists. |

Links can be used once, and expire after `ACCOUNT_LINK_TIMEOUT_SECONDS` (3 days by default). The rate limit is the `registration` scope: 10 per hour per IP address.

The links point at `FRONTEND_BASE_URL`: `/accept-invite?uid=…&token=…` and `/verify-email?uid=…&token=…`. The frontend posts the `uid` and `token` back to the endpoints above.

## Membership plans

| Method and path | Who | Notes |
|---|---|---|
| `GET membership/plans/` | Anyone | Active plans only. Each has `price`, `currency` (ETB or USD), `price_display` (e.g. `ETB 1,250.00`), `duration_months`, `loan_limit`, `restricted_archive_access`, `benefits` and `requires_documents`. |
| `GET`, `POST membership/manage/plans/`<br>`GET`, `PUT`, `PATCH membership/manage/plans/{id}/` | Manager, system administrator | Retire a plan with `is_active: false`. Plans can't be deleted. |

Membership plans are also the member categories (ILMDAS-33). Plan prices are [TBC] in the SRS (ILMDAS-117).

## Membership requests

| Method and path | Who | Notes |
|---|---|---|
| `POST membership/requests/` | Signed-in account | Body: `{"plan": "<slug>"}`. Status `awaiting_payment`. The price is fixed when the request is made. An account can have one open request at a time, and none while it has a current membership. |
| `POST membership/requests/{id}/documents/` | The request's owner | Multipart field `file`: PDF, JPEG or PNG, up to 5 MB, at most 5 per request. The type is checked from the file content. |
| `GET membership/me/` | Signed-in account | `isMember`, the current `subscription`, and the account's `requests`. |

## Staff approval queue (librarian, manager, system administrator)

| Method and path | Body | Notes |
|---|---|---|
| `GET membership/manage/requests/?status=` | | Default `awaiting_approval`. The other statuses are `awaiting_payment`, `approved` and `rejected`. |
| `POST membership/manage/requests/{id}/payment/` | `method` (`cash`, `bank_transfer`, `telebirr`, `cbe_birr`, `card`, `other`), `reference` | Records the payment by hand. Status becomes `awaiting_approval`. |
| `POST membership/manage/requests/{id}/approve/` | | Needs a recorded payment, plus at least one document if the plan requires documents. Starts the subscription and grants `member`. |
| `POST membership/manage/requests/{id}/reject/` | `reason` | The account stays a guest. If the request was already paid, refunds follow ILMDAS-118. |

The payment providers (Telebirr, CBE Birr and cards, ILMDAS-544 to 546) will call `apps.membership.services.record_payment` from their verified callbacks. That is the same function that staff use today.

## Expiry

Run `python manage.py expire_memberships` daily, for example from cron. It ends subscriptions whose period is over and removes the member role, unless the account has another current subscription. Running it more than once is safe. Renewal is ILMDAS-547.

## Audit events

| Area | Events |
|---|---|
| Accounts | `account.staff.created`, `account.invite.accepted`, `account.registered`, `account.email_verified` |
| Roles | `role.assigned` (from staff registration and from approval) |
| Plans | `membership.plan.created`, `membership.plan.updated`, `membership.plan.retired` |
| Requests | `membership.requested`, `membership.document_uploaded`, `membership.payment_recorded`, `membership.approved`, `membership.rejected` |
| Expiry | `membership.expired` |

## Email settings

Emails go through Django's email backend, which is the provider adapter. The provider itself is decision ILMDAS-119.

| Environment | Default backend |
|---|---|
| Development | Console: emails are printed in the backend logs (`docker compose -f docker-compose.dev.yml logs -f backend`). |
| Production | SMTP |

The settings are `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`, `FRONTEND_BASE_URL` and `ACCOUNT_LINK_TIMEOUT_SECONDS`. They are listed in `backend/.env.example`.
