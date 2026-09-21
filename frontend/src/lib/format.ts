export const numberFormat = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 1,
});

export function gaugeFillPercent(value: number, cap: number): number {
  if (!(cap > 0)) {
    return 0;
  }
  return Math.min(100, Math.max(0, (value / cap) * 100));
}

export function lightLabel(light: "green" | "yellow" | "red"): string {
  switch (light) {
    case "green":
      return "Green";
    case "yellow":
      return "Yellow";
    case "red":
      return "Red";
  }
}
