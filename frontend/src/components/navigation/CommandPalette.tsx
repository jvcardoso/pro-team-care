import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Command, Clock, TrendingUp, X } from "lucide-react";
import api from "../../services/api";
import { notify } from "../../utils/notifications";

interface SearchResult {
  shortcode: string;
  label: string;
  description?: string;
  route: string;
  icon?: string;
  module_code: string;
  program_type: string;
  match_type: string;
  relevance_score: number;
}

interface SearchResponse {
  query: string;
  execution_type: "direct" | "select";
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTimeMs, setSearchTimeMs] = useState<number>(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Focar input quando abrir
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Resetar ao fechar
  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setResults([]);
      setSelectedIndex(0);
      setSearchTimeMs(0);
    }
  }, [isOpen]);

  // Buscar com debounce
  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const timeoutId = setTimeout(() => {
      performSearch(query);
    }, 200);

    return () => clearTimeout(timeoutId);
  }, [query]);

  // Scroll para item selecionado
  useEffect(() => {
    if (resultsRef.current) {
      const selectedElement = resultsRef.current.children[
        selectedIndex
      ] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({
          block: "nearest",
          behavior: "smooth",
        });
      }
    }
  }, [selectedIndex]);

  const performSearch = async (searchQuery: string) => {
    try {
      setIsLoading(true);
      const response = await api.post<SearchResponse>(
        "/api/v1/program-codes/quick-search",
        {
          query: searchQuery,
        }
      );

      const data = response.data;
      setSearchTimeMs(data.search_time_ms);

      console.log("🔍 DEBUG COMPLETO:");
      console.log("  Query:", searchQuery);
      console.log("  Execution type:", data.execution_type);
      console.log("  Total results:", data.total_results);
      console.log("  Results:", JSON.stringify(data.results, null, 2));

      // Se for execução direta (código exato), navegar imediatamente
      if (data.execution_type === "direct" && data.results.length === 1) {
        console.log("✅ NAVEGAÇÃO DIRETA DETECTADA");
        console.log("  Destino:", data.results[0].route);
        console.log("  Label:", data.results[0].label);
        handleSelect(data.results[0]);
      } else {
        console.log("📋 MODO SELEÇÃO - mostrando lista de resultados");
        setResults(data.results);
        setSelectedIndex(0);
      }
    } catch (error: any) {
      console.error("Erro na busca:", error);
      if (error.response?.status !== 404) {
        notify.error("Erro ao buscar códigos");
      }
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = async (result: SearchResult) => {
    try {
      // Registrar uso para analytics
      await api.post("/api/v1/program-codes/register-usage", {
        shortcode: result.shortcode,
      });

      // Navegar para a rota
      navigate(result.route);

      // Fechar modal
      onClose();

      // Notificação opcional
      // notify.success(`Navegando para ${result.label}`);
    } catch (error) {
      console.error("Erro ao registrar uso:", error);
      // Navegar mesmo se falhar o registro
      navigate(result.route);
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (results[selectedIndex]) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case "Escape":
        e.preventDefault();
        onClose();
        break;
    }
  };

  const getModuleColor = (moduleCode: string): string => {
    const colors: Record<string, string> = {
      EM: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
      ES: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
      US: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
      PE: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
      CL: "bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300",
      PR: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300",
      CT: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
      AM: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
      FS: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
      DS: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900 dark:text-cyan-300",
      RE: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
    };
    return (
      colors[moduleCode] ||
      "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
    );
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 dark:bg-black/70 z-50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl w-full max-w-2xl mx-4 overflow-hidden border border-gray-200 dark:border-gray-700">
          {/* Header com Input */}
          <div className="flex items-center gap-3 p-4 border-b border-gray-200 dark:border-gray-700">
            <Search className="w-5 h-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite código (ex: em0001) ou nome (ex: empresa)..."
              className="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 text-lg"
            />
            {isLoading && (
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent" />
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Results */}
          <div ref={resultsRef} className="max-h-[60vh] overflow-y-auto">
            {query.length < 2 ? (
              // Empty state
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                <Command className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">
                  Digite pelo menos 2 caracteres para buscar
                </p>
                <div className="mt-4 text-xs space-y-1">
                  <p>✨ Exemplos:</p>
                  <p>
                    <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                      em0001
                    </kbd>{" "}
                    - Código direto
                  </p>
                  <p>
                    <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                      empresa
                    </kbd>{" "}
                    - Busca por nome
                  </p>
                </div>
              </div>
            ) : results.length === 0 && !isLoading ? (
              // No results
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Nenhum resultado encontrado para "{query}"</p>
                <p className="text-xs mt-2">Tente outro termo ou código</p>
              </div>
            ) : (
              // Results list
              <div className="py-2">
                {results.map((result, index) => (
                  <button
                    key={result.shortcode}
                    onClick={() => handleSelect(result)}
                    className={`
                      w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700/50
                      ${
                        index === selectedIndex
                          ? "bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-500"
                          : ""
                      }
                      transition-colors
                    `}
                  >
                    {/* Module Badge */}
                    <div
                      className={`px-2 py-1 rounded text-xs font-mono font-semibold ${getModuleColor(
                        result.module_code
                      )}`}
                    >
                      {result.shortcode}
                    </div>

                    {/* Content */}
                    <div className="flex-1 text-left min-w-0">
                      <div className="font-medium text-gray-900 dark:text-white truncate">
                        {result.label}
                      </div>
                      {result.description && (
                        <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          {result.description}
                        </div>
                      )}
                    </div>

                    {/* Match type indicator */}
                    {result.match_type === "exact" && (
                      <div className="text-xs text-green-600 dark:text-green-400 font-semibold">
                        EXATO
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {results.length > 0 && (
            <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <div>
                {results.length} resultado{results.length !== 1 ? "s" : ""} em{" "}
                {searchTimeMs.toFixed(0)}ms
              </div>
              <div className="flex gap-3">
                <span>
                  <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
                    ↑↓
                  </kbd>{" "}
                  Navegar
                </span>
                <span>
                  <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
                    Enter
                  </kbd>{" "}
                  Abrir
                </span>
                <span>
                  <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
                    Esc
                  </kbd>{" "}
                  Fechar
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default CommandPalette;
