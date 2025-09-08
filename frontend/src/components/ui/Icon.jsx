/**
 * Componente Icon - Wrapper para ícones Lucide React
 * Fornece fallback seguro para ícones não encontrados
 */

import React from "react";
import * as LucideIcons from "lucide-react";

/**
 * Componente Icon
 *
 * @param {string} name - Nome do ícone (sem 'Icon' no final)
 * @param {number} size - Tamanho do ícone (padrão: 24)
 * @param {string} className - Classes CSS adicionais
 * @param {Object} props - Outras props passadas para o ícone
 */
export const Icon = ({ name, size = 24, className = "", ...props }) => {
  if (!name) {
    return (
      <div
        className={`w-[${size}px] h-[${size}px] bg-gray-300 rounded ${className}`}
        style={{ width: size, height: size }}
        title="Ícone não especificado"
        {...props}
      />
    );
  }

  // Mapeamento de ícones para corrigir nomes incorretos
  const iconMapping = {
    'database': 'Database',
    'user': 'User',
    'users': 'Users',
    'settings': 'Settings',
    'home': 'Home',
    'menu': 'Menu',
    'search': 'Search',
    'plus': 'Plus',
    'edit': 'Edit',
    'trash': 'Trash',
    'eye': 'Eye',
    'eye-off': 'EyeOff',
    'check': 'Check',
    'x': 'X',
    'arrow-left': 'ArrowLeft',
    'arrow-right': 'ArrowRight',
    'chevron-down': 'ChevronDown',
    'chevron-up': 'ChevronUp',
    'chevron-left': 'ChevronLeft',
    'chevron-right': 'ChevronRight'
  };

  // Usar mapeamento ou nome original
  const iconName = iconMapping[name] || name;

  // Tentar encontrar o ícone
  const IconComponent = LucideIcons[iconName];

  if (!IconComponent) {
    // Fallback para ícone não encontrado
    console.warn(`Ícone não encontrado: ${name}`);

    return (
      <div
        className={`w-[${size}px] h-[${size}px] bg-gray-300 rounded flex items-center justify-center ${className}`}
        style={{ width: size, height: size }}
        title={`Ícone não encontrado: ${name}`}
        {...props}
      >
        <span className="text-xs text-gray-600">?</span>
      </div>
    );
  }

  return <IconComponent size={size} className={className} {...props} />;
};

export default Icon;
