import React from "react";
import { Heart, Code } from "lucide-react";

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-3 px-4 sm:px-6 lg:px-8 flex-shrink-0">
      <div className="flex flex-col sm:flex-row items-center justify-between text-sm text-gray-500 dark:text-gray-400">
        {/* Left side - Copyright */}
        <div className="flex items-center space-x-1 mb-2 sm:mb-0">
          <span>Copyright © {currentYear}</span>
          <strong className="text-blue-600 dark:text-blue-400">
            Pro Team Care
          </strong>
          <span className="hidden md:inline">
            - Sistemas para Cuidados de Saúde e Bem Estar da Pessoa
          </span>
        </div>

        {/* Right side - Version & Credits */}
        <div className="flex items-center space-x-4">
          {/* Version */}
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-medium">
              v1.0.0
            </span>
            <span className="hidden sm:inline text-xs">Build 2024</span>
          </div>

          {/* Made with love */}
          <div className="flex items-center space-x-1">
            <span className="hidden md:inline text-xs">Feito com</span>
            <Heart className="w-3 h-3 text-red-500 fill-current" />
            <span className="hidden lg:inline text-xs">e</span>
            <Code className="w-3 h-3 text-blue-500" />
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
