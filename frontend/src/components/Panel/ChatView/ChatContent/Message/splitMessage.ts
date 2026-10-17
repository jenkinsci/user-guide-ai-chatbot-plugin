export interface MessagePiece {
  kind: "text" | "code";
  content: string;
  language?: string;
}

interface OpenFence {
  marker: string;
  indent: number;
  language: string;
  lines: string[];
}

const FENCE_LINE = /^([ \t]*)(`{3,}|~{3,})(.*)$/;

function openFence(line: string): OpenFence | null {
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
    language: info.trim().split(/\s+/)[0],
    lines: [],
  };
}

function closesFence(line: string, fence: OpenFence): boolean {
  const trimmed = line.trim();
  return (
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
      content: open.lines.join("\n").trimEnd(),

      language: open.language,
    });

  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (fence) {
      if (closesFence(line, fence)) {
        flushCode(fence);

        fence = null;
      } else {
        fence.lines.push(stripIndent(line, fence.indent));
      }

      continue;
    }

    const opened = i < lines.length - 1 ? openFence(line) : null;

    if (opened) {

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
