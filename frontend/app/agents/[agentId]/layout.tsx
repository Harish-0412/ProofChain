export function generateStaticParams() {
  return Array.from({ length: 22 }, (_, index) => ({
    agentId: String(index + 1),
  }));
}

export default function AgentDetailLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return children;
}
