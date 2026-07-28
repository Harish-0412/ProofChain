import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ProofChain - Accreditation Evidence Integrity & Governance",
  description:
    "ProofChain orchestrates 22 governed AI agents to collect, validate, map, and audit accreditation evidence with tamper-evident integrity and deterministic traceability.",
  keywords: [
    "accreditation",
    "evidence",
    "audit",
    "NAAC",
    "governance",
    "ProofChain",
    "agentic",
    "AI",
  ],
};

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
