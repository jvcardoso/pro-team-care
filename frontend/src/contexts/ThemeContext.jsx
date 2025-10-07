import React, { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext({
  theme: "light",
  toggleTheme: () => {},
  isDark: false,
});

export const ThemeProvider = ({ children }) => {
  // Inicializar com valor do localStorage imediatamente (síncrono)
  const getInitialTheme = () => {
    const savedTheme = localStorage.getItem("pro-team-care-theme");
    console.log(
      "🎨 ThemeContext: Carregando tema inicial do localStorage:",
      savedTheme
    );
    if (savedTheme) {
      return savedTheme;
    }
    // Verificar preferência do sistema
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
    const systemTheme = prefersDark ? "dark" : "light";
    console.log("🎨 ThemeContext: Usando preferência do sistema:", systemTheme);
    return systemTheme;
  };

  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    console.log("🎨 ThemeContext: Aplicando tema:", theme);

    // Aplicar tema usando Tailwind CSS class system
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }

    // Salvar no localStorage
    localStorage.setItem("pro-team-care-theme", theme);
    console.log("🎨 ThemeContext: Tema salvo no localStorage:", theme);
  }, [theme]);

  // Listener para mudanças no localStorage (sincronização entre abas)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "pro-team-care-theme" && e.newValue) {
        setTheme(e.newValue);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => {
      const newTheme = prev === "light" ? "dark" : "light";
      console.log("🎨 ThemeContext: Alternando tema:", prev, "→", newTheme);
      return newTheme;
    });
  };

  const value = {
    theme,
    toggleTheme,
    isDark: theme === "dark",
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};

export default ThemeContext;
