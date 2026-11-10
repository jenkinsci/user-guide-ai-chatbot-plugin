export interface MessagePiece {
  kind: "text" | "code";
  content: string;
  language?: string;
}

interface OpenFence {
  marker: string;
  indent: number;
  listIndent: number;
  quote: number;
  language: string;
  lines: string[];
}

const QUOTE_MARKER = /^[ \t]{0,3}>[ \t]?/;
const FENCE_LINE = /^([ \t]*(?:(?:[-*+]|\d{1,9}[.)])[ \t]+)?)(`{3,}|~{3,})(.*)$/;
const LIST_ITEM = /^[ \t]*(?:[-*+]|\d{1,9}[.)])[ \t]+/;
const TAB_SIZE = 4;

function stripQuote(line: string, depth: number): string {
  for (let n = 0; n < depth; n++) {
    line = line.replace(QUOTE_MARKER, "");
  }
  return line;
}

function widthOf(text: string): number {
  let width = 0;
  for (const char of text) {
    width += char === "\t" ? TAB_SIZE - (width % TAB_SIZE) : 1;
  }
  return width;
}

function indentOf(line: string): number {
  return widthOf(line.slice(0, line.length - line.trimStart().length));
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
    indent: widthOf(indent),
    listIndent: 0,
    quote,
    language: info.trim().split(/\s+/)[0],
    lines: [],
  };
}

function closeFence(line: string, fence: OpenFence): boolean {
  const trimmed = line.trim();
  const indent = indentOf(line);
  return (
    indent <= fence.indent + 3 &&
    trimmed.length >= fence.marker.length &&
    trimmed === fence.marker[0].repeat(trimmed.length)
  );
}

function findListIndent(
  lines: string[],
  end: number,
  fence: OpenFence,
): number {
  for (let i = end - 1; i >= 0; i--) {
    const line = stripQuote(lines[i], fence.quote);
    const indent = indentOf(line);
    if (line.trim() === "" || indent >= fence.indent) {
      continue;
    }
    const match = LIST_ITEM.exec(line);
    if (!match || widthOf(match[0]) > fence.indent) {
      return 0;
    }
    return widthOf(match[0]);
  }
  return 0;
}

function leaveListItem(line: string, fence: OpenFence): boolean {
  const indent = indentOf(line);
  return (
    line.trim() !== "" &&
    indent < fence.listIndent &&
    !closeFence(line, fence)
  );
}

function stripIndent(line: string, width: number): string {
  let cut = 0;
  while (
    widthOf(line.slice(0, cut)) < width &&
    (line[cut] === " " || line[cut] === "\t")
  ) {
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
      let inner = line;
      let quote = 0;
      while (quote < fence.quote && QUOTE_MARKER.test(inner)) {
        inner = inner.replace(QUOTE_MARKER, "");
        quote++;
      }
      const codeStarted = fence.lines.some((code) => code.trim() !== "");
      if (!codeStarted && leaveListItem(inner, fence)) {
        fence.listIndent = 0;
      }
      if (quote < fence.quote || leaveListItem(inner, fence)) {
        flushCode(fence);
        fence = null;
      } else {
        if (closeFence(inner, fence)) {
          flushCode(fence);
          fence = null;
        } else {
          fence.lines.push(stripIndent(inner, fence.indent));
        }
        continue;
      }
    }

    const opened = i < lines.length - 1 ? openFence(line) : null;

    if (opened) {
      const listMarker = stripQuote(line, opened.quote)
        .split(opened.marker)[0]
        .trim();
      if (listMarker) {
        textLines.push(listMarker);
      }
      flushText();
      opened.listIndent = listMarker
        ? opened.indent
        : findListIndent(lines, i, opened);
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
