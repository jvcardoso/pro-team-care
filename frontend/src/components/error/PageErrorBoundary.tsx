import React, { ReactNode } from "react";
import ErrorBoundary from "./ErrorBoundary";

interface PageErrorBoundaryProps {
  children: ReactNode;
  pageName?: string;
}

const PageErrorBoundary: React.FC<PageErrorBoundaryProps> = ({
  children,
  pageName,
}) => {
  const handleError = (error: Error) => {
    console.error(`[PAGE] Error in ${pageName || "unknown page"}:`, error);

    // TODO: Send to error tracking service with page context
    // analytics.track('page_error', {
    //   pageName,
    //   message: error.message,
    //   stack: error.stack,
    //   timestamp: new Date().toISOString()
    // });
  };

  return (
    <ErrorBoundary level="page" onError={handleError}>
      {children}
    </ErrorBoundary>
  );
};

export default PageErrorBoundary;
