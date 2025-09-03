/**
 * Hook para melhorar navegação por teclado
 * Fornece utilities para gerenciamento de foco e navegação acessível
 */

import { useEffect, useCallback } from "react";

const useKeyboardNavigation = () => {
  // Focus no primeiro elemento focalizável de um container
  const focusFirstElement = useCallback((containerRef) => {
    if (!containerRef.current) return;

    const focusableElements = containerRef.current.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
  }, []);

  // Focus no último elemento focalizável de um container
  const focusLastElement = useCallback((containerRef) => {
    if (!containerRef.current) return;

    const focusableElements = containerRef.current.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length > 0) {
      focusableElements[focusableElements.length - 1].focus();
    }
  }, []);

  // Trap focus dentro de um modal/dialog
  const trapFocus = useCallback((containerRef) => {
    if (!containerRef.current) return () => {};

    const handleKeyDown = (e) => {
      if (e.key !== "Tab") return;

      const focusableElements = containerRef.current.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Navegar entre elementos com setas
  const handleArrowNavigation = useCallback(
    (e, items, currentIndex, onIndexChange) => {
      if (
        ![
          "ArrowUp",
          "ArrowDown",
          "ArrowLeft",
          "ArrowRight",
          "Home",
          "End",
        ].includes(e.key)
      ) {
        return false;
      }

      e.preventDefault();
      let newIndex = currentIndex;

      switch (e.key) {
        case "ArrowUp":
        case "ArrowLeft":
          newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
          break;
        case "ArrowDown":
        case "ArrowRight":
          newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
          break;
        case "Home":
          newIndex = 0;
          break;
        case "End":
          newIndex = items.length - 1;
          break;
        default:
          return false;
      }

      if (onIndexChange) {
        onIndexChange(newIndex);
      }

      // Focus no novo elemento se existir
      if (items[newIndex] && items[newIndex].focus) {
        items[newIndex].focus();
      }

      return true;
    },
    []
  );

  // Esc para fechar modals/dropdowns
  const handleEscapeKey = useCallback((callback) => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        callback();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Anunciar mudanças para screen readers
  const announceToScreenReader = useCallback((message, priority = "polite") => {
    const announcement = document.createElement("div");
    announcement.setAttribute("aria-live", priority);
    announcement.setAttribute("aria-atomic", "true");
    announcement.className = "sr-only";
    announcement.textContent = message;

    document.body.appendChild(announcement);

    // Remove após um tempo para não poluir o DOM
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  // Focus management para SPAs
  const manageFocus = useCallback(
    (
      elementId,
      fallbackSelector = 'h1, [role="heading"][aria-level="1"], main'
    ) => {
      // Tentar focar no elemento especificado
      if (elementId) {
        const element = document.getElementById(elementId);
        if (element) {
          element.focus();
          return;
        }
      }

      // Fallback para primeiro heading ou main
      const fallbackElement = document.querySelector(fallbackSelector);
      if (fallbackElement) {
        fallbackElement.setAttribute("tabindex", "-1");
        fallbackElement.focus();
      }
    },
    []
  );

  return {
    focusFirstElement,
    focusLastElement,
    trapFocus,
    handleArrowNavigation,
    handleEscapeKey,
    announceToScreenReader,
    manageFocus,
  };
};

export default useKeyboardNavigation;
