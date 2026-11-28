export function readStreamLines(buffer: string): {
  payloads: string[];
  rest: string;
} {
  const lines = buffer.split("\n");
  const rest = lines.pop() || "";
  const payloads = lines
    .map((line) => line.trim())
    .filter((line) => line !== "")
    .map((line) =>
      line.startsWith("data: ") ? line.replace(/^data:\s*/, "") : line,
    )
    .filter((line) => line !== "[DONE]");
  return { payloads, rest };
}
