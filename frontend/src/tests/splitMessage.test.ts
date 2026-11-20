import { describe, expect, test } from "vitest";
import { splitMessage } from "../components/Panel/ChatView/ChatContent/Message/splitMessage";

const FENCE = "```";

describe("splitMessage", () => {
  describe("basics", () => {
    test("returns a plain text as a single text piece", () => {
      expect(splitMessage("How can I create a new Plugin?")).toEqual([
        { kind: "text", content: "How can I create a new Plugin?" },
      ]);
    });
    test("returns no piece for empty string", () => {
      expect(splitMessage("")).toEqual([]);
    });
    test("splits text around single code block and keeps its language", () => {
      const msg = `Before\n${FENCE}groovy\necho 'hi'\n${FENCE}\nAfter`;

      expect(splitMessage(msg)).toEqual([
        { kind: "text", content: "Before" },
        { kind: "code", content: "echo 'hi'", language: "groovy" },
        { kind: "text", content: "After" },
      ]);
    });
    test("uses an empty language when the code fence omits one", () => {
      const msg = `${FENCE}\nx = 1\n${FENCE}`;
      expect(splitMessage(msg)).toEqual([
        { kind: "code", content: "x = 1", language: "" },
      ]);
    });
  });

  describe("language tags", () => {
    test("keeps a language tag with a plus sign", () => {
      const msg = `${FENCE}c++\nint a;\n${FENCE}\nAfter`;
      expect(splitMessage(msg)).toEqual([
        { kind: "code", content: "int a;", language: "c++" },
        { kind: "text", content: "After" },
      ]);
    });
    test("keeps a language tag with a hyphen", () => {
      const msg = `${FENCE}shell-session\n$ ls\n${FENCE}`;
      expect(splitMessage(msg)).toEqual([
        { kind: "code", content: "$ ls", language: "shell-session" },
      ]);
    });
  });

  describe("closing fence", () => {
    test("does not close on a fence indented inside the code block", () => {
      const code = `def s = """\n        ${FENCE}\n"""`;
      const msg = `${FENCE}groovy\n${code}\n${FENCE}\nAfter`;

      expect(splitMessage(msg)).toEqual([
        { kind: "code", content: code, language: "groovy" },
        { kind: "text", content: "After" },
      ]);
    });
    test("supports tilde fences", () => {
      expect(splitMessage("~~~\na\n~~~")).toEqual([
        { kind: "code", content: "a", language: "" },
      ]);
    });
    test("does not close a longer fence with a shorter one", () => {
      const longFence = "````";
      const msg = `${longFence}\na\n${FENCE}\nstill code\n${longFence}`;
      expect(splitMessage(msg)).toEqual([
        { kind: "code", content: `a\n${FENCE}\nstill code`, language: "" },
      ]);
    });
  });

  describe("blockquotes", () => {
    test("ends the code block when the quote ends", () => {
      const msg = `> ${FENCE}sh\n> echo hi\nAfter the quote`;
      expect(splitMessage(msg)).toEqual([
        { kind: "code", content: "echo hi", language: "sh" },
        { kind: "text", content: "After the quote" },
      ]);
    });
  });

  describe("indentation and lists", () => {
    test("keeps unindented lines after an indented code fence outside the list", () => {
      const msg = `  ${FENCE}groovy\npipeline {\n}\n  ${FENCE}`;

      expect(splitMessage(msg)).toEqual([
        { kind: "code", content: "pipeline {\n}", language: "groovy" },
      ]);
    });
    test("removes the list indent from code inside a list item", () => {
      const msg = `1. Run this:\n   ${FENCE}sh\n   make\n   ${FENCE}\n2. Next`;

      expect(splitMessage(msg)).toEqual([
        { kind: "text", content: "1. Run this:" },
        { kind: "code", content: "make", language: "sh" },
        { kind: "text", content: "2. Next" },
      ]);
    });
  });

  describe("edge cases", () => {
    test("runs an unclosed code block to the end of the message", () => {
      const msg = `Text\n${FENCE}sh\nmake`;

      expect(splitMessage(msg)).toEqual([
        { kind: "text", content: "Text" },
        { kind: "code", content: "make", language: "sh" },
      ]);
    });

    test("keeps fence on the last line as text", () => {
      const msg = `Text\n${FENCE}`;

      expect(splitMessage(msg)).toEqual([{ kind: "text", content: msg }]);
    });

    test("handles Windows line endings", () => {
      const msg = `A\r\n${FENCE}sh\r\nmake\r\n${FENCE}\r\nB`;

      expect(splitMessage(msg)).toEqual([
        { kind: "text", content: "A" },
        { kind: "code", content: "make", language: "sh" },
        { kind: "text", content: "B" },
      ]);
    });

    test("does not open a backtick fence whose info string has a backtick", () => {
      const msg = `${FENCE}a\`b\nnot code\n${FENCE}`;

      expect(splitMessage(msg)).toEqual([{ kind: "text", content: msg }]);
    });

    test("keeps tab indentation inside code", () => {
      const msg = `${FENCE}\n\tindented\n${FENCE}`;

      expect(splitMessage(msg)).toEqual([
        { kind: "code", content: "\tindented", language: "" },
      ]);
    });
  });
});
