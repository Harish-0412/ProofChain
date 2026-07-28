import { AppShell } from "@/components/layout/app-shell";

export default function SectionLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
