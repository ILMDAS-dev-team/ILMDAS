import type { Metadata } from "next"
import { Ubuntu } from "next/font/google"
import { AuthProvider } from "@/context/AuthContext"
import "./globals.css"

const ubuntu = Ubuntu({
  subsets: ["latin"],
  weight: ["300", "400", "500", "700"],
  display: "swap",
})

export const metadata: Metadata = {
  title: "ILMDAS",
  description: "Integrated Library Management and Digital Archive System",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={ubuntu.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
