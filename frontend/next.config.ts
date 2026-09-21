import { createTheme } from "@mui/material/styles";
import { withPigment } from "@pigment-css/nextjs-plugin";
import type { NextConfig } from "next";

import { tokens } from "./src/theme/tokens";

const api = process.env.API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    optimizePackageImports: ["@mui/material"],
  },
  async rewrites() {
    return [
      { source: "/health", destination: `${api}/health` },
      { source: "/api/:path*", destination: `${api}/api/:path*` },
    ];
  },
};

const theme = createTheme({
  cssVariables: true,
  palette: {
    background: { default: tokens.mist, paper: tokens.paper },
    text: { primary: tokens.ink, secondary: tokens.mute },
    primary: { main: tokens.bar, contrastText: tokens.paper },
    success: { main: tokens.go, contrastText: tokens.paper },
    warning: { main: tokens.caution, contrastText: tokens.ink },
    error: { main: tokens.halt, contrastText: tokens.paper },
    divider: tokens.steel,
  },
  shape: { borderRadius: 2 },
  typography: {
    fontFamily: 'var(--font-body), "Atkinson Hyperlegible", sans-serif',
  },
});

export default withPigment(nextConfig, {
  theme,
  transformLibraries: ["@mui/material-pigment-css"],
});
