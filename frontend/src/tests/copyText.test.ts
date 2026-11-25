// @vitest-environment jsdom
import { afterEach, describe, expect, test, vi } from "vitest";
import { copyText } from "../components/Panel/ChatView/ChatContent/Message/copyText";

function setClipboard(writeText?: (text: string) => Promise<void>) {
  Object.defineProperty(window, "isSecureContext", {
    value: writeText !== undefined,
    configurable: true,
  });
  Object.defineProperty(navigator, "clipboard", {
    value: writeText ? { writeText } : undefined,
    configurable: true,
  });
}

function setExecCommand(execCommand: () => boolean) {
  Object.defineProperty(document, "execCommand", {
    value: vi.fn(execCommand),
    configurable: true,
  });
}

afterEach(() => {
  document.body.innerHTML = "";
});

describe("copyText", () => {
  test("uses the Clipboard API when it is available", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    setClipboard(writeText);
    setExecCommand(() => true);

    expect(await copyText("plugin")).toBe(true);
    expect(writeText).toHaveBeenCalledWith("plugin");
    expect(document.execCommand).not.toHaveBeenCalled();
  });

  test("falls back to execCommand when the Clipboard API fails", async () => {
    setClipboard(vi.fn().mockRejectedValue(new Error("denied")));
    setExecCommand(() => true);

    expect(await copyText("plugin")).toBe(true);
    expect(document.execCommand).toHaveBeenCalledWith("copy");
  });

  test("copies the text through a hidden textarea without the Clipboard API", async () => {
    setClipboard();
    let copied = "";
    setExecCommand(() => {
      copied = document.querySelector("textarea")?.value ?? "";
      return true;
    });

    expect(await copyText("plugin")).toBe(true);
    expect(copied).toBe("plugin");
  });

  test("returns what execCommand returns", async () => {
    setClipboard();
    setExecCommand(() => false);

    expect(await copyText("plugin")).toBe(false);
  });

  test("returns false when execCommand throws", async () => {
    setClipboard();
    setExecCommand(() => {
      throw new Error("not supported");
    });

    expect(await copyText("plugin")).toBe(false);
  });

  test("removes the textarea and restores focus after copying", async () => {
    setClipboard();

    setExecCommand(() => {
      document.querySelector("textarea")?.focus();
      return true;
    });
    const button = document.createElement("button");
    document.body.appendChild(button);
    button.focus();

    await copyText("plugin");

    expect(document.querySelector("textarea")).toBeNull();
    expect(document.activeElement).toBe(button);
  });
});
