import React, { ReactNode } from "react";
import ErrorBoundary from "./ErrorBoundary";

interface AppErrorBoundaryProps {
  children: ReactNode;
}

const AppErrorBoundary: React.FC<AppErrorBoundaryProps> = ({ children }) => {
  const handleError = (error: Error) => {
    // Log application-level errors
    console.error("[APP] Application error:", error);

    // TODO: Send to error tracking service
    // analytics.track('app_error', {
    //   message: error.message,
    //   stack: error.stack,
    //   timestamp: new Date().toISOString()
    // });
  };

  return (
    <ErrorBoundary level="app" onError={handleError}>
      {children}
    </ErrorBoundary>
  );
};

export default AppErrorBoundary;
