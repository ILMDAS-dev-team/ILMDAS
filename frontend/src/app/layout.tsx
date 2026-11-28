import type { Metadata } from "next"
import { Ubuntu } from "next/font/google"
import { AuthProvider } from "@/context/AuthContext"
import { LanguageProvider } from "@/context/LanguageContext"
import { PROJECT_FULL_NAME } from "@/lib/brand"
import "./globals.css"

const ubuntu = Ubuntu({
  subsets: ["latin"],
  weight: ["300", "400", "500", "700"],
  display: "swap",
})

export const metadata: Metadata = {
  title: PROJECT_FULL_NAME,
  description: `Integrated Library Management and Digital Archive System — ${PROJECT_FULL_NAME}`,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={ubuntu.className}>
        <AuthProvider>
          <LanguageProvider>{children}</LanguageProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
