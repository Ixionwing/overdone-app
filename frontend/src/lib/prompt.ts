export function requirePrompt(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) {
    throw new Error(
      "Enter a proposed increment, then try Evaluate Increment again.",
    );
  }
  return trimmed;
}
