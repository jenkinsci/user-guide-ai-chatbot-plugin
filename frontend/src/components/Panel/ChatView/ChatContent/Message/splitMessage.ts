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

const QUOTE_MARKER = /^([ \t]{0,3}>)([ \t]?)/;
const FENCE_LINE = /^([ \t]*(?:(?:[-*+]|\d{1,9}[.)])[ \t]+)?)(`{3,}|~{3,})(.*)$/;
const LIST_ITEM = /^[ \t]*(?:[-*+]|\d{1,9}[.)])[ \t]+/;
const TAB_SIZE = 4;

function widthOf(text: string, start = 0): number {
  let column = start;
  for (const char of text) {
    column += char === "\t" ? TAB_SIZE - (column % TAB_SIZE) : 1;
  }
  return column - start;
}

function stripQuotes(line: string, max: number): [string, number] {
  let depth = 0;
  let column = 0;
  for (; depth < max; depth++) {
    const match = QUOTE_MARKER.exec(line);
    if (!match) {
      break;
    }
    const [marker, lead, gap] = match;
    column += widthOf(lead, column);
    const kept = gap === "\t" ? widthOf(gap, column) - 1 : 0;
    column += gap.length;
    line = " ".repeat(kept) + line.slice(marker.length);
  }
  return [line, depth];
}

function indentOf(line: string): number {
  return widthOf(line.slice(0, line.length - line.trimStart().length));
}

function openFence(line: string): OpenFence | null {
  const [inner, quote] = stripQuotes(line, Infinity);
  const match = FENCE_LINE.exec(inner);
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
    const [line] = stripQuotes(lines[i], fence.quote);
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
  return line.trim() !== "" && indentOf(line) < fence.listIndent;
}

function stripIndent(line: string, width: number): string {
  let cut = 0;
  let column = 0;
  while (column < width && (line[cut] === " " || line[cut] === "\t")) {
    column += widthOf(line[cut], column);
    cut++;
  }
  return " ".repeat(Math.max(0, column - width)) + line.slice(cut);
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
    const first = open.lines.find((code) => code.trim() !== "");
    const width =
      first === undefined
        ? open.indent
        : Math.min(open.indent, indentOf(first));
    pieces.push({
      kind: "code",
      content: open.lines.map((code) => stripIndent(code, width)).join("\n"),
      language: open.language,
    });
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (fence) {
      const [inner, quote] = stripQuotes(line, fence.quote);
      if (closeFence(inner, fence)) {
        flushCode(fence);
        fence = null;
        continue;
      }
      const codeStarted = fence.lines.some((code) => code.trim() !== "");
      if (!codeStarted && leaveListItem(inner, fence)) {
        fence.listIndent = 0;
      }
      if (quote === fence.quote && !leaveListItem(inner, fence)) {
        fence.lines.push(inner);
        continue;
      }
      flushCode(fence);
      fence = null;
    }

    const opened = i < lines.length - 1 ? openFence(line) : null;

    if (opened) {
      const listMarker = stripQuotes(line, opened.quote)[0]
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
