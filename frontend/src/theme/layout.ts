import { css } from "@pigment-css/react";

import { tokens } from "@/theme/tokens";

export const col = css({
  display: "flex",
  flexDirection: "column",
  gap: 12,
  minWidth: 0,
});

export const row = css({
  display: "flex",
  flexDirection: "row",
  flexWrap: "wrap",
  alignItems: "center",
  gap: 12,
  minWidth: 0,
});

export const displayHeading = css({
  fontFamily: "var(--font-display), Tektur, sans-serif",
  fontSize: "1.15rem",
  letterSpacing: "0.03em",
  margin: 0,
  textWrap: "balance",
});

export const pageMain = css({
  maxWidth: 1120,
  margin: "0 auto",
  padding: "1.5rem 1.25rem 3rem",
});

export const pageTitle = css({
  fontFamily: "var(--font-display), Tektur, sans-serif",
  fontSize: "clamp(2rem, 5vw, 3rem)",
  letterSpacing: "0.06em",
  margin: "0 0 0.35rem",
  lineHeight: 1,
});

export const pageLead = css({
  margin: "0 0 1.75rem",
  color: tokens.mute,
  maxWidth: "40rem",
});

export const rail = css({
  backgroundColor: tokens.paper,
  borderLeft: `4px solid ${tokens.bar}`,
  padding: 16,
  minWidth: 0,
});

export const field = css({
  display: "flex",
  flexDirection: "column",
  gap: 6,
  minWidth: 0,
});

export const label = css({
  fontWeight: 700,
});

export const textarea = css({
  width: "100%",
  minWidth: 0,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
  fontSize: "0.85rem",
  lineHeight: 1.45,
  padding: "0.65rem 0.75rem",
  color: tokens.ink,
  backgroundColor: tokens.paper,
  border: `1px solid ${tokens.steel}`,
  borderRadius: 2,
  resize: "vertical",
  whiteSpace: "pre",
  overflowX: "auto",
  overflowWrap: "normal",
  "&:hover": {
    borderColor: tokens.bar,
  },
  "&:focus-visible": {
    outline: `2px solid ${tokens.bar}`,
    outlineOffset: 2,
  },
});

export const promptArea = css({
  fontFamily: 'var(--font-body), "Atkinson Hyperlegible", sans-serif',
  fontSize: "1rem",
  whiteSpace: "pre-wrap",
  overflowWrap: "break-word",
});

export const button = css({
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "0.5rem 0.9rem",
  border: `1px solid ${tokens.bar}`,
  borderRadius: 2,
  backgroundColor: tokens.bar,
  color: tokens.paper,
  cursor: "pointer",
  fontFamily: "inherit",
  fontWeight: 700,
  "&:hover": {
    backgroundColor: tokens.barHover,
  },
  "&:focus-visible": {
    outline: `2px solid ${tokens.bar}`,
    outlineOffset: 3,
  },
  "&:disabled": {
    opacity: 0.6,
    cursor: "wait",
  },
});

export const buttonQuiet = css({
  backgroundColor: "transparent",
  color: tokens.bar,
  "&:hover": {
    backgroundColor: tokens.mist,
  },
});

export const alert = css({
  padding: "0.65rem 0.75rem",
  borderLeft: `4px solid ${tokens.halt}`,
  backgroundColor: tokens.alertWash,
  color: tokens.ink,
  margin: 0,
  overflowWrap: "anywhere",
});

export const warning = css({
  padding: "0.65rem 0.75rem",
  borderLeft: `4px solid ${tokens.caution}`,
  backgroundColor: tokens.warningWash,
  color: tokens.ink,
  margin: 0,
  overflowWrap: "anywhere",
});

export const mute = css({
  color: tokens.mute,
  margin: 0,
});
