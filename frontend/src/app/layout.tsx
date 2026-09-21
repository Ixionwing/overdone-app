import type { CSSProperties } from "react";
import type { Metadata, Viewport } from "next";
import { Atkinson_Hyperlegible, Tektur } from "next/font/google";

import "@mui/material-pigment-css/styles.css";
import "./globals.css";
import { tokens } from "@/theme/tokens";

const display = Tektur({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const body = Atkinson_Hyperlegible({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-body",
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: tokens.mist,
};

export const metadata: Metadata = {
  title: "Overdone",
  description: "Local diagnostic scratchpad for workout increment risk",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${body.variable}`}
      style={
        {
          "--color-mist": tokens.mist,
          "--color-paper": tokens.paper,
          "--color-ink": tokens.ink,
          "--color-bar": tokens.bar,
        } as CSSProperties
      }
    >
      <body>
        <a className="skip-link" href="#main">
          Skip to Main Content
        </a>
        {children}
      </body>
    </html>
  );
}
