import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_PAGES === "true";
const repositoryName =
  process.env.GITHUB_REPOSITORY?.split("/")[1] || "ProofChain";
const pagesBasePath =
  process.env.PAGES_BASE_PATH ||
  (isGitHubPages ? `/${repositoryName}` : "");

const nextConfig: NextConfig = {
  ...(isGitHubPages
    ? {
        output: "export" as const,
        basePath: pagesBasePath,
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {
        async rewrites() {
          const gatewayOrigin =
            process.env.PROOFCHAIN_GATEWAY_ORIGIN || "http://127.0.0.1:8000";
          return [
            {
              source: "/proofchain-data/:path*",
              destination: `${gatewayOrigin}/ui-api/:path*`,
            },
          ];
        },
      }),
};

export default nextConfig;
