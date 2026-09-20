import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
