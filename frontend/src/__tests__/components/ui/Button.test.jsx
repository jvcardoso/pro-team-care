/**
 * Testes para components/ui/Button.jsx
 * Testes para componente base Button - Prioridade 2
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import Button from "../../../components/ui/Button";

describe("Button Component", () => {
  describe("Basic Rendering", () => {
    test("should render button with text", () => {
      render(<Button>Click me</Button>);

      const button = screen.getByRole("button", { name: /click me/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent("Click me");
    });

    test("should render button with correct type", () => {
      render(<Button type="submit">Submit</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("type", "submit");
    });

    test("should render button with default type", () => {
      render(<Button>Default</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("type", "button");
    });
  });

  describe("Variants", () => {
    test("should render primary variant by default", () => {
      render(<Button>Primary</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("bg-primary-500");
    });

    test("should render secondary variant", () => {
      render(<Button variant="secondary">Secondary</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("bg-secondary-500");
    });

    test("should render success variant", () => {
      render(<Button variant="success">Success</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("bg-green-500");
    });

    test("should render danger variant", () => {
      render(<Button variant="danger">Danger</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("bg-red-500");
    });

    test("should render warning variant", () => {
      render(<Button variant="warning">Warning</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("bg-yellow-500");
    });
  });

  describe("Sizes", () => {
    test("should render medium size by default", () => {
      render(<Button>Medium</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("px-4", "py-2.5", "min-h-[40px]");
    });

    test("should render small size", () => {
      render(<Button size="sm">Small</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("px-3", "py-2", "min-h-[36px]");
    });

    test("should render large size", () => {
      render(<Button size="lg">Large</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("px-6", "py-3", "min-h-[44px]");
    });
  });

  describe("States", () => {
    test("should render disabled state", () => {
      render(<Button disabled>Disabled</Button>);

      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
      expect(button).toHaveClass(
        "disabled:opacity-50",
        "disabled:pointer-events-none"
      );
    });

    test("should render loading state", () => {
      render(<Button loading>Loading</Button>);

      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
      expect(button).toHaveClass("disabled:opacity-50");
    });

    test("should show loading state classes when loading", () => {
      render(<Button loading>Loading</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("relative", "pointer-events-none");
    });
  });

  describe("Outline Variant", () => {
    test("should render outline primary", () => {
      render(<Button outline>Outline Primary</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("border-primary-500", "text-primary-500");
    });

    test("should render outline secondary", () => {
      render(
        <Button variant="secondary" outline>
          Outline Secondary
        </Button>
      );

      const button = screen.getByRole("button");
      expect(button).toHaveClass("border-secondary-500", "text-secondary-500");
    });
  });

  describe("Block Variant", () => {
    test("should render full width when block is true", () => {
      render(<Button block>Block Button</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("w-full");
    });
  });

  describe("Custom Classes", () => {
    test("should apply custom className", () => {
      render(<Button className="custom-class">Custom</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("custom-class");
    });
  });

  describe("Event Handling", () => {
    test("should call onClick when clicked", () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click me</Button>);

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test("should not call onClick when disabled", () => {
      const handleClick = jest.fn();
      render(
        <Button onClick={handleClick} disabled>
          Click me
        </Button>
      );

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    test("should not call onClick when loading", () => {
      const handleClick = jest.fn();
      render(
        <Button onClick={handleClick} loading>
          Click me
        </Button>
      );

      const button = screen.getByRole("button");
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe("Icons", () => {
    test("should render icon on left by default", () => {
      const TestIcon = () => <span data-testid="test-icon">Icon</span>;
      render(<Button icon={<TestIcon />}>With Icon</Button>);

      const icon = screen.getByTestId("test-icon");
      const button = screen.getByRole("button");

      expect(icon).toBeInTheDocument();
      expect(button).toContainElement(icon);
    });

    test("should render icon on right when specified", () => {
      const TestIcon = () => <span data-testid="test-icon">Icon</span>;
      render(
        <Button icon={<TestIcon />} iconPosition="right">
          With Icon
        </Button>
      );

      const icon = screen.getByTestId("test-icon");
      expect(icon).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    test("should be keyboard accessible", () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Accessible</Button>);

      const button = screen.getByRole("button");
      button.focus();
      expect(document.activeElement).toBe(button);
    });

    test("should have focus styles", () => {
      render(<Button>Focusable</Button>);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("focus:ring-2", "focus:ring-offset-2");
    });

    test("should support ARIA attributes", () => {
      render(
        <Button aria-label="Save document" aria-describedby="save-description">
          Save
        </Button>
      );

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("aria-label", "Save document");
      expect(button).toHaveAttribute("aria-describedby", "save-description");
    });
  });

  describe("Props Forwarding", () => {
    test("should forward additional props", () => {
      render(
        <Button
          data-testid="custom-button"
          data-analytics="button-click"
          title="Custom tooltip"
        >
          Custom Props
        </Button>
      );

      const button = screen.getByTestId("custom-button");
      expect(button).toHaveAttribute("data-analytics", "button-click");
      expect(button).toHaveAttribute("title", "Custom tooltip");
    });
  });

  describe("Edge Cases", () => {
    test("should handle empty children", () => {
      render(<Button></Button>);

      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
      expect(button.textContent.trim()).toBe("");
    });

    test("should handle null children", () => {
      render(<Button>{null}</Button>);

      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
    });

    test("should handle multiple children", () => {
      render(
        <Button>
          <span>First</span>
          <span>Second</span>
        </Button>
      );

      const button = screen.getByRole("button");
      expect(button).toHaveTextContent("FirstSecond");
    });
  });
});
