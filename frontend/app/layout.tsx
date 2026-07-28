import type { Metadata } from "next";
import "./globals.css";
import { AppProviders } from "@/components/providers/app-providers";

export const metadata: Metadata = {
  title: {
    template: "%s | ProofChain",
    default: "ProofChain - Governed Accreditation Evidence Intelligence",
  },
  description:
    "A plain-language accreditation readiness dashboard showing the work, decisions, pending actions, and governed outputs of 22 ProofChain agents.",
  keywords: ["accreditation", "evidence", "audit", "NAAC", "governance", "ProofChain", "agentic"],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <a href="#main-content" className="skip-link">Skip to main content</a>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
