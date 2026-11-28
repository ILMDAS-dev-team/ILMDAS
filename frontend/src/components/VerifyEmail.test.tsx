import { fireEvent, render, screen } from "@testing-library/react"
import { VerifyEmail } from "@/components/VerifyEmail"
import { ApiRequestError } from "@/lib/apiErrors"

jest.mock("@/lib/registration", () => ({
  verifyEmail: jest.fn(),
  resendVerification: jest.fn(),
}))

import { resendVerification, verifyEmail } from "@/lib/registration"

beforeEach(() => jest.clearAllMocks())

test("verifies the link once and offers sign-in", async () => {
  ;(verifyEmail as jest.Mock).mockResolvedValue({ detail: "ok" })
  render(<VerifyEmail uid="MQ" token="abc" />)

  expect(await screen.findByRole("status")).toHaveTextContent("Your email is verified")
  expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/login")
  expect(verifyEmail).toHaveBeenCalledTimes(1)
  expect(verifyEmail).toHaveBeenCalledWith("MQ", "abc")
})

test("an expired link shows the error and lets the person request a new one", async () => {
  ;(verifyEmail as jest.Mock).mockRejectedValue(
    new ApiRequestError("This link is invalid or has expired.", 400, {
      token: "This link is invalid or has expired.",
    })
  )
  ;(resendVerification as jest.Mock).mockResolvedValue({
    detail: "If a pending account uses this email, a new link has been sent.",
  })
  render(<VerifyEmail uid="MQ" token="old" />)

  expect(await screen.findByRole("alert")).toHaveTextContent("invalid or has expired")
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: "chaltu@example.org" },
  })
  fireEvent.click(screen.getByRole("button", { name: "Send a new link" }))

  expect(await screen.findByRole("status")).toHaveTextContent("a new link has been sent")
  expect(resendVerification).toHaveBeenCalledWith("chaltu@example.org")
})

test("an incomplete link is reported without calling the API", () => {
  render(<VerifyEmail uid="" token="" />)
  expect(screen.getByRole("alert")).toHaveTextContent("This link is incomplete")
  expect(verifyEmail).not.toHaveBeenCalled()
})
