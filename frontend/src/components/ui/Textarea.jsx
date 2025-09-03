import React, { forwardRef } from "react";
import { Star } from "lucide-react";

const Textarea = forwardRef(
  (
    {
      label,
      error,
      helper,
      required = false,
      size = "md",
      variant = "default",
      className = "",
      containerClassName = "",
      rows = 4,
      resize = true,
      ...props
    },
    ref
  ) => {
    const textareaClasses = [
      "w-full px-3 py-2 border rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2",
      "bg-input text-foreground placeholder-muted-foreground",
      "border-border focus:border-ring focus:ring-ring",

      // Size variants
      size === "sm" && "text-sm",
      size === "md" && "text-sm",
      size === "lg" && "text-base",

      // Variant styles
      variant === "default" && "border-border",
      variant === "success" &&
        "border-green-500 focus:border-green-500 focus:ring-green-500",
      variant === "warning" &&
        "border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500",
      variant === "error" &&
        "border-red-500 focus:border-red-500 focus:ring-red-500",

      error && "border-red-500 focus:border-red-500 focus:ring-red-500",
      !resize && "resize-none",
      className,
    ]
      .filter(Boolean)
      .join(" ");

    const containerClasses = ["w-full", containerClassName]
      .filter(Boolean)
      .join(" ");

    return (
      <div className={containerClasses}>
        {label && (
          <label className="flex items-center text-sm font-medium text-foreground mb-2">
            {label}
            {required && (
              <Star className="h-3 w-3 text-red-500 ml-1 fill-current" />
            )}
          </label>
        )}

        <textarea
          ref={ref}
          rows={rows}
          className={textareaClasses}
          {...props}
        />

        {error && <p className="mt-1 text-sm text-red-500">{error}</p>}

        {helper && !error && (
          <p className="mt-1 text-sm text-muted-foreground">{helper}</p>
        )}
      </div>
    );
  }
);

Textarea.displayName = "Textarea";

export default Textarea;
