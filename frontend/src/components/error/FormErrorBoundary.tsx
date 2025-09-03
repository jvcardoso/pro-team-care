import React, { ReactNode } from "react";
import ErrorBoundary from "./ErrorBoundary";

interface FormErrorBoundaryProps {
  children: ReactNode;
  formName?: string;
}

const FormErrorBoundary: React.FC<FormErrorBoundaryProps> = ({
  children,
  formName,
}) => {
  const handleError = (error: Error) => {
    console.error(`[FORM] Error in ${formName || "unknown form"}:`, error);

    // TODO: Send to error tracking service with form context
    // analytics.track('form_error', {
    //   formName,
    //   message: error.message,
    //   stack: error.stack,
    //   timestamp: new Date().toISOString()
    // });
  };

  return (
    <ErrorBoundary level="form" onError={handleError}>
      {children}
    </ErrorBoundary>
  );
};

export default FormErrorBoundary;
