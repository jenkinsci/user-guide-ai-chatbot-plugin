import { describe, expect, test } from "vitest";
import { readStreamLines } from "../components/Panel/ChatView/readStreamLines";

describe("readStreamLines", () => {
  test("strips the data prefix from a complete line", () => {
    const buffer = 'data: {"event": "started", "qa_pair_id": 5}\n\n';

    expect(readStreamLines(buffer)).toEqual({
      payloads: ['{"event": "started", "qa_pair_id": 5}'],
      rest: "",
    });
  });

  test("returns every line of a chunk in order", () => {
    const buffer =
      'data: {"content": "Hello"}\n\ndata: {"content": " Jenkins"}\n\n';

    expect(readStreamLines(buffer).payloads).toEqual([
      '{"content": "Hello"}',
      '{"content": " Jenkins"}',
    ]);
  });

  test("keeps an unfinished line for the next chunk", () => {
    const first = readStreamLines('data: {"content": "Jen');

    expect(first).toEqual({ payloads: [], rest: 'data: {"content": "Jen' });

    const second = readStreamLines(first.rest + 'kins"}\n\n');

    expect(second).toEqual({ payloads: ['{"content": "Jenkins"}'], rest: "" });
  });

  test("skips the blank lines", () => {
    expect(readStreamLines("\n\n   \n").payloads).toEqual([]);
  });

  test("skips the DONE marker", () => {
    const buffer = 'data: {"event": "done"}\n\ndata: [DONE]\n\n';

    expect(readStreamLines(buffer).payloads).toEqual(['{"event": "done"}']);
  });

  test("keeps the line that has no data prefix", () => {
    expect(readStreamLines('{"event": "chunk"}\n').payloads).toEqual([
      '{"event": "chunk"}',
    ]);
  });
});
