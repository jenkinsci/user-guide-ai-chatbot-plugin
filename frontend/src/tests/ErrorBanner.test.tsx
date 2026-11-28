// @vitest-environment jsdom
import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import ErrorBanner from "../components/ErrorBanner";

afterEach(cleanup);

describe("ErrorBanner", () => {
  test("shows nothing when there is no message", () => {
    render(<ErrorBanner message={null} handleCloseError={vi.fn()} />);

    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("shows the error message", () => {
    render(
      <ErrorBanner message="Failed to send!" handleCloseError={vi.fn()} />,
    );

    expect(screen.getByRole("alert").textContent).toContain("Failed to send!");
  });

  test("calls handleCloseError when the close button is clicked", () => {
    const handleCloseError = vi.fn();
    render(
      <ErrorBanner
        message="Failed to send!"
        handleCloseError={handleCloseError}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(handleCloseError).toHaveBeenCalled();
  });
});
