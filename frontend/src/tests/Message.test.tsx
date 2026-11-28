// @vitest-environment jsdom
import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import Message from "../components/Panel/ChatView/ChatContent/Message/Message";
import { AnswerEntity, QuestionEntity } from "../models/models";

const data = {
  id: 1,
  content: "Why is my build Failing?",
  created_at: "2026-06-07T10:00:00Z",
};

afterEach(cleanup);

describe("Message", () => {
  describe("question", () => {
    test("opens an edit box with the current text", () => {
      render(
        <Message message={new QuestionEntity(data)} onEditConfirm={vi.fn()} />,
      );

      fireEvent.click(screen.getByTitle("Edit Button"));

      expect(screen.getByRole("textbox")).toHaveProperty("value", data.content);
    });

    test("confirms the trimmed text on Enter", () => {
      const onEditConfirm = vi.fn();
      const question = new QuestionEntity(data);
      render(<Message message={question} onEditConfirm={onEditConfirm} />);

      fireEvent.click(screen.getByTitle("Edit Button"));
      const input = screen.getByRole("textbox");
      fireEvent.change(input, { target: { value: "  How to fix this  " } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onEditConfirm).toHaveBeenCalledWith(question, "How to fix this");
      expect(screen.queryByRole("textbox")).toBeNull();
    });

    test("does not confirm an empty edit", () => {
      const onEditConfirm = vi.fn();
      render(
        <Message
          message={new QuestionEntity(data)}
          onEditConfirm={onEditConfirm}
        />,
      );

      fireEvent.click(screen.getByTitle("Edit Button"));
      const input = screen.getByRole("textbox");
      fireEvent.change(input, { target: { value: "   " } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onEditConfirm).not.toHaveBeenCalled();
    });

    test("cancels the edit when Escape is pressed", () => {
      const onEditConfirm = vi.fn();
      render(
        <Message
          message={new QuestionEntity(data)}
          onEditConfirm={onEditConfirm}
        />,
      );

      fireEvent.click(screen.getByTitle("Edit Button"));
      const input = screen.getByRole("textbox");
      fireEvent.change(input, { target: { value: "Something else" } });
      fireEvent.keyDown(input, { key: "Escape" });

      expect(onEditConfirm).not.toHaveBeenCalled();
      expect(screen.queryByRole("textbox")).toBeNull();
      expect(screen.getByText(data.content)).toBeDefined();
    });
  });

  describe("answer", () => {
    test("calls onRetry when retry is clicked", () => {
      const onRetry = vi.fn();
      render(<Message message={new AnswerEntity(data)} onRetry={onRetry} />);

      fireEvent.click(screen.getByTitle("Retry Button"));

      expect(onRetry).toHaveBeenCalled();
    });

    test("shows a check icon after copying", async () => {
      Object.defineProperty(window, "isSecureContext", {
        value: true,
        configurable: true,
      });
      Object.defineProperty(navigator, "clipboard", {
        value: { writeText: vi.fn().mockResolvedValue(undefined) },
        configurable: true,
      });
      render(<Message message={new AnswerEntity(data)} onRetry={vi.fn()} />);

      fireEvent.click(screen.getByTestId("ContentCopyIcon"));

      expect(await screen.findByTestId("CheckIcon")).toBeDefined();
    });
  });
});
