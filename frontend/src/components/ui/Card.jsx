import React from "react";

const Card = React.memo(
  ({
    children,
    className = "",
    title,
    subtitle,
    actions,
    noPadding = false,
    shadow = true,
    ...props
  }) => {
    const baseClasses = [
      "bg-card text-card-foreground rounded-lg border border-border",
      shadow && "shadow-sm",
      className,
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <div className={baseClasses} {...props}>
        {(title || subtitle || actions) && (
          <div className="px-6 py-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div>
                {title && (
                  <h3 className="text-lg font-semibold text-card-foreground">
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {subtitle}
                  </p>
                )}
              </div>
              {actions && (
                <div className="flex items-center space-x-2">{actions}</div>
              )}
            </div>
          </div>
        )}
        <div className={noPadding ? "" : "px-6 py-4"}>{children}</div>
      </div>
    );
  }
);

Card.displayName = "Card";

export default Card;
