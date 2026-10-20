export interface MessagePiece {
  kind: "text" | "code";
  content: string;
  language?: string;
}

interface OpenFence {
  marker: string;
  indent: number;
  quote: number;
  language: string;
  lines: string[];
}

const QUOTE_MARKER = /^[ \t]{0,3}>[ \t]?/;
const FENCE_LINE = /^([ \t]*(?:(?:[-*+]|\d{1,9}[.)])[ \t]+)?)(`{3,}|~{3,})(.*)$/;

function stripQuote(line: string, depth: number): string {
  for (let n = 0; n < depth; n++) {
    line = line.replace(QUOTE_MARKER, "");
  }
  return line;
}

function openFence(line: string): OpenFence | null {
  let quote = 0;
  while (QUOTE_MARKER.test(line)) {
    line = line.replace(QUOTE_MARKER, "");
    quote++;
  }
  const match = FENCE_LINE.exec(line);
  if (!match) {
    return null;
  }
  const [, indent, marker, info] = match;

  if (marker[0] === "`" && info.includes("`")) {
    return null;
  }
  return {
    marker,
    indent: indent.length,
    quote,
    language: info.trim().split(/\s+/)[0],
    lines: [],
  };
}

function closesFence(line: string, fence: OpenFence): boolean {
  const trimmed = line.trim();
  const indent = line.length - line.trimStart().length;
  return (
    indent <= fence.indent + 3 &&
    trimmed.length >= fence.marker.length &&
    trimmed === fence.marker[0].repeat(trimmed.length)
  );
}

function stripIndent(line: string, width: number): string {
  let cut = 0;
  while (cut < width && (line[cut] === " " || line[cut] === "\t")) {
    cut++;
  }
  return line.slice(cut);
}

export function splitMessage(text: string): MessagePiece[] {
  const pieces: MessagePiece[] = [];
  const lines = text.split(/\r?\n/);
  let textLines: string[] = [];
  let fence: OpenFence | null = null;

  const flushText = () => {
    const content = textLines.join("\n").trim();
    if (content) {
      pieces.push({ kind: "text", content });
    }
    textLines = [];
  };

  const flushCode = (open: OpenFence) => {
    pieces.push({
      kind: "code",
      content: open.lines.join("\n"),
      language: open.language,
    });
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (fence) {
      const inner = stripQuote(line, fence.quote);
      if (closesFence(inner, fence)) {
        flushCode(fence);
        fence = null;
      } else {
        fence.lines.push(stripIndent(inner, fence.indent));
      }
      continue;
    }

    const opened = i < lines.length - 1 ? openFence(line) : null;

    if (opened) {
      const listMarker = stripQuote(line, opened.quote)
        .slice(0, opened.indent)
        .trim();
      if (listMarker) {
        textLines.push(listMarker);
      }
      flushText();
      fence = opened;
    } else {
      textLines.push(line);
    }
  }
  if (fence) {
    flushCode(fence);
  }
  flushText();
  return pieces;
}
