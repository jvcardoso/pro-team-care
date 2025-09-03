import { useCallback } from "react";

interface UseErrorHandlerOptions {
  onError?: (error: Error) => void;
  level?: "app" | "page" | "form" | "component";
}

export const useErrorHandler = (options: UseErrorHandlerOptions = {}) => {
  const { onError, level = "component" } = options;

  const handleError = useCallback(
    (error: Error, context?: string) => {
      console.error(
        `[${level.toUpperCase()}] Error${context ? ` in ${context}` : ""}:`,
        error
      );

      // Call custom error handler if provided
      if (onError) {
        onError(error);
      }

      // Log to error tracking service in production
      if (process.env.NODE_ENV === "production") {
        // TODO: Integrate with error tracking service
        console.error("Production error logged:", {
          message: error.message,
          stack: error.stack,
          level,
          context,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
        });
      }
    },
    [level, onError]
  );

  const handleAsyncError = useCallback(
    async <T>(
      asyncOperation: () => Promise<T>,
      context?: string
    ): Promise<T | null> => {
      try {
        return await asyncOperation();
      } catch (error) {
        handleError(error as Error, context);
        return null;
      }
    },
    [handleError]
  );

  const handleSyncError = useCallback(
    <T>(operation: () => T, context?: string): T | null => {
      try {
        return operation();
      } catch (error) {
        handleError(error as Error, context);
        return null;
      }
    },
    [handleError]
  );

  return {
    handleError,
    handleAsyncError,
    handleSyncError,
  };
};

export default useErrorHandler;
