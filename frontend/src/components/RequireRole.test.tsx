import { render, screen } from "@testing-library/react"
import { RequireRole } from "@/components/RequireRole"
import AccessDenied from "@/components/AccessDenied"

jest.mock("@/context/AuthContext", () => ({
  useAuth: jest.fn(),
}))

import { useAuth } from "@/context/AuthContext"

const mockUser = {
  id: 1,
  username: "admin",
  email: "admin@example.com",
  roles: [{ code: "system_administrator", name: "System Administrator" }],
}

const mockMemberUser = {
  id: 2,
  username: "member",
  email: "member@example.com",
  roles: [{ code: "member", name: "Member" }],
}

describe("AccessDenied", () => {
  test("renders access denied message", () => {
    render(<AccessDenied />)
    expect(screen.getByRole("heading", { name: "Access Denied" })).toBeInTheDocument()
    expect(screen.getByText(/You are not authorized/)).toBeInTheDocument()
  })
})

describe("RequireRole", () => {
  const TestComponent = () => <div data-testid="protected-content">Protected</div>

  test("shows children when user has required role", () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: mockUser,
      loading: false,
    })
    render(
      <RequireRole role="system_administrator">
        <TestComponent />
      </RequireRole>
    )
    expect(screen.getByTestId("protected-content")).toBeInTheDocument()
  })

  test("shows AccessDenied when user does not have required role", () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: mockMemberUser,
      loading: false,
    })
    render(
      <RequireRole role="system_administrator">
        <TestComponent />
      </RequireRole>
    )
    expect(screen.queryByTestId("protected-content")).not.toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Access Denied" })).toBeInTheDocument()
  })

  test("requires staff when requireStaff is true and user is staff", () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: mockUser,
      loading: false,
    })
    render(
      <RequireRole requireStaff>
        <TestComponent />
      </RequireRole>
    )
    expect(screen.getByTestId("protected-content")).toBeInTheDocument()
  })

  test("denies access when requireStaff is true and user is not staff", () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: mockMemberUser,
      loading: false,
    })
    render(
      <RequireRole requireStaff>
        <TestComponent />
      </RequireRole>
    )
    expect(screen.queryByTestId("protected-content")).not.toBeInTheDocument()
  })

  test("shows loading state when loading is true", () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      loading: true,
    })
    render(
      <RequireRole role="system_administrator">
        <TestComponent />
      </RequireRole>
    )
    expect(screen.getByText("Loading...")).toBeInTheDocument()
  })
})

describe("RequireRole when signed out", () => {
  test("shows access denied instead of loading forever", () => {
    ;(useAuth as jest.Mock).mockReturnValue({ user: null, loading: false })
    render(
      <RequireRole requireStaff>
        <div data-testid="protected-content">Protected</div>
      </RequireRole>
    )
    expect(screen.getByText("Access Denied")).toBeInTheDocument()
    expect(screen.queryByText("Loading...")).toBeNull()
    expect(screen.queryByTestId("protected-content")).toBeNull()
  })
})
