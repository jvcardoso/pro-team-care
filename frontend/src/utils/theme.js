/**
 * Theme Utilities and Helpers
 * Provides programmatic access to theme values and utilities
 */

import { designTokens } from "../styles/design-tokens";

/**
 * Get color value from theme
 * @param {string} color - Color name (e.g., 'primary', 'success')
 * @param {string|number} shade - Color shade (e.g., '500', 500)
 * @returns {string} Color value or CSS variable
 */
export const getColor = (color, shade = null) => {
  if (shade) {
    return `var(--${color}-${shade})`;
  }

  // Return main color variable
  const colorMap = {
    primary: "var(--primary-color)",
    secondary: "var(--secondary-color)",
    success: "var(--success-color)",
    danger: "var(--danger-color)",
    warning: "var(--warning-color)",
    info: "var(--info-color)",
    light: "var(--light-color)",
    dark: "var(--dark-color)",
  };

  return colorMap[color] || `var(--${color}-color)`;
};

/**
 * Get spacing value
 * @param {string|number} size - Spacing size
 * @returns {string} Spacing value
 */
export const getSpacing = (size) => {
  const spacing = designTokens.spacing[size];
  return spacing || `${size}rem`;
};

/**
 * Get font size value
 * @param {string} size - Font size name
 * @returns {string} Font size value
 */
export const getFontSize = (size) => {
  return designTokens.typography.fontSize[size] || size;
};

/**
 * Get font weight value
 * @param {string} weight - Font weight name
 * @returns {string} Font weight value
 */
export const getFontWeight = (weight) => {
  return designTokens.typography.fontWeight[weight] || weight;
};

/**
 * Get breakpoint value
 * @param {string} breakpoint - Breakpoint name
 * @returns {string} Breakpoint value
 */
export const getBreakpoint = (breakpoint) => {
  return designTokens.layout.screens[breakpoint] || breakpoint;
};

/**
 * Get shadow value
 * @param {string} shadow - Shadow name
 * @returns {string} Shadow value
 */
export const getShadow = (shadow) => {
  return designTokens.boxShadow[shadow] || shadow;
};

/**
 * Get border radius value
 * @param {string} radius - Radius name
 * @returns {string} Border radius value
 */
export const getBorderRadius = (radius) => {
  return designTokens.borderRadius[radius] || radius;
};

/**
 * Get z-index value
 * @param {string} layer - Z-index layer name
 * @returns {string|number} Z-index value
 */
export const getZIndex = (layer) => {
  return designTokens.zIndex[layer] || layer;
};

/**
 * Generate responsive classes
 * @param {string} property - CSS property
 * @param {string} value - CSS value
 * @param {string[]} breakpoints - Breakpoints to generate for
 * @returns {object} Responsive class object
 */
export const generateResponsiveClasses = (
  property,
  value,
  breakpoints = ["sm", "md", "lg", "xl"]
) => {
  const classes = {
    [property]: value,
  };

  breakpoints.forEach((bp) => {
    classes[`${bp}:${property}`] = value;
  });

  return classes;
};

/**
 * Create utility classes object
 * @param {string} prefix - Class prefix
 * @param {object} values - Values object
 * @param {string} property - CSS property name
 * @returns {object} Utility classes object
 */
export const createUtilityClasses = (prefix, values, property) => {
  const classes = {};

  Object.entries(values).forEach(([key, value]) => {
    const className = key === "default" ? prefix : `${prefix}-${key}`;
    classes[className] = { [property]: value };
  });

  return classes;
};

/**
 * Get theme variable name
 * @param {string} variable - Variable name
 * @returns {string} CSS custom property name
 */
export const getThemeVariable = (variable) => {
  return `var(--${variable})`;
};

/**
 * Check if dark theme is active
 * @returns {boolean} True if dark theme is active
 */
export const isDarkTheme = () => {
  if (typeof window === "undefined") return false;

  const theme = localStorage.getItem("pro-team-care-theme");
  if (theme) {
    return theme === "dark";
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches;
};

/**
 * Get current theme
 * @returns {string} Current theme ('light' or 'dark')
 */
export const getCurrentTheme = () => {
  if (typeof window === "undefined") return "light";

  const theme = localStorage.getItem("pro-team-care-theme");
  if (theme) {
    return theme;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
};

/**
 * Set theme programmatically
 * @param {string} theme - Theme to set ('light' or 'dark')
 */
export const setTheme = (theme) => {
  if (typeof window === "undefined") return;

  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("pro-team-care-theme", theme);

  // Dispatch custom event for theme change
  window.dispatchEvent(
    new CustomEvent("themeChange", {
      detail: { theme },
    })
  );
};

/**
 * Toggle theme
 * @returns {string} New theme value
 */
export const toggleTheme = () => {
  const currentTheme = getCurrentTheme();
  const newTheme = currentTheme === "light" ? "dark" : "light";
  setTheme(newTheme);
  return newTheme;
};

/**
 * Listen to theme changes
 * @param {function} callback - Callback function to execute on theme change
 * @returns {function} Cleanup function
 */
export const onThemeChange = (callback) => {
  if (typeof window === "undefined") return () => {};

  const handleThemeChange = (event) => {
    callback(event.detail.theme);
  };

  window.addEventListener("themeChange", handleThemeChange);

  // Also listen to system theme changes
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const handleSystemThemeChange = (e) => {
    const savedTheme = localStorage.getItem("pro-team-care-theme");
    if (!savedTheme) {
      callback(e.matches ? "dark" : "light");
    }
  };

  mediaQuery.addEventListener("change", handleSystemThemeChange);

  return () => {
    window.removeEventListener("themeChange", handleThemeChange);
    mediaQuery.removeEventListener("change", handleSystemThemeChange);
  };
};

/**
 * Create CSS-in-JS theme object
 * @param {string} theme - Theme name ('light' or 'dark')
 * @returns {object} Theme object for CSS-in-JS
 */
export const createThemeObject = (theme = getCurrentTheme()) => {
  return {
    colors: {
      primary: getColor("primary"),
      secondary: getColor("secondary"),
      success: getColor("success"),
      danger: getColor("danger"),
      warning: getColor("warning"),
      info: getColor("info"),
      light: getColor("light"),
      dark: getColor("dark"),
    },
    spacing: designTokens.spacing,
    typography: designTokens.typography,
    layout: designTokens.layout,
    shadows: designTokens.boxShadow,
    borderRadius: designTokens.borderRadius,
    zIndex: designTokens.zIndex,
    breakpoints: designTokens.layout.screens,
  };
};

/**
 * Create media query helper
 * @param {string} breakpoint - Breakpoint name
 * @returns {string} Media query string
 */
export const mediaQuery = (breakpoint) => {
  const size = getBreakpoint(breakpoint);
  return `@media (min-width: ${size})`;
};

/**
 * Create hover styles helper
 * @param {object} styles - Styles object
 * @returns {object} Styles with hover state
 */
export const createHoverStyles = (styles) => {
  return {
    ...styles,
    "&:hover": {
      ...styles.hover,
    },
  };
};

/**
 * Create focus styles helper
 * @param {object} styles - Styles object
 * @returns {object} Styles with focus state
 */
export const createFocusStyles = (styles) => {
  return {
    ...styles,
    "&:focus": {
      outline: "none",
      boxShadow: `0 0 0 0.2rem ${getColor("primary", "200")}`,
      ...styles.focus,
    },
  };
};

export default {
  getColor,
  getSpacing,
  getFontSize,
  getFontWeight,
  getBreakpoint,
  getShadow,
  getBorderRadius,
  getZIndex,
  generateResponsiveClasses,
  createUtilityClasses,
  getThemeVariable,
  isDarkTheme,
  getCurrentTheme,
  setTheme,
  toggleTheme,
  onThemeChange,
  createThemeObject,
  mediaQuery,
  createHoverStyles,
  createFocusStyles,
};
