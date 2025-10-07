// OPÇÕES DE VISUALIZAÇÃO PARA COLUNA "ENTIDADES"
// Substitua a seção atual (linhas 62-97) por uma dessas opções:

// ========================= OPÇÃO 1: BADGES COLORIDOS =========================
// Visual mais moderno com badges coloridos em linha horizontal
{
  key: "establishments_count",
  label: "Entidades",
  type: "custom",
  render: (value, item) => (
    <div className="flex flex-wrap gap-1">
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
        <Building className="w-3 h-3 mr-1" />
        {item.establishments_count || 0}
      </span>
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        <Users className="w-3 h-3 mr-1" />
        {item.clients_count || 0}
      </span>
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
        <UserCheck className="w-3 h-3 mr-1" />
        {item.professionals_count || 0}
      </span>
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
        <User className="w-3 h-3 mr-1" />
        {item.users_count || 0}
      </span>
    </div>
  ),
},

// ======================= OPÇÃO 2: LINHA HORIZONTAL COMPACTA =======================
// Icons coloridos em linha horizontal, sem fundo
{
  key: "establishments_count",
  label: "Entidades",
  type: "custom",
  render: (value, item) => (
    <div className="flex items-center space-x-3 text-sm">
      <span className="flex items-center text-blue-600 dark:text-blue-400">
        <Building className="w-3 h-3 mr-1" />
        <span className="font-medium">{item.establishments_count || 0}</span>
      </span>
      <span className="flex items-center text-green-600 dark:text-green-400">
        <Users className="w-3 h-3 mr-1" />
        <span className="font-medium">{item.clients_count || 0}</span>
      </span>
      <span className="flex items-center text-purple-600 dark:text-purple-400">
        <UserCheck className="w-3 h-3 mr-1" />
        <span className="font-medium">{item.professionals_count || 0}</span>
      </span>
      <span className="flex items-center text-gray-600 dark:text-gray-400">
        <User className="w-3 h-3 mr-1" />
        <span className="font-medium">{item.users_count || 0}</span>
      </span>
    </div>
  ),
},

// ========================= OPÇÃO 3: GRID 2x2 COMPACTO =========================
// Layout em grid 2x2, muito compacto
{
  key: "establishments_count",
  label: "Entidades",
  type: "custom",
  render: (value, item) => (
    <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
      <div className="flex items-center text-blue-600 dark:text-blue-400">
        <Building className="w-3 h-3 mr-1" />
        <span className="font-medium">{item.establishments_count || 0}</span>
      </div>
      <div className="flex items-center text-green-600 dark:text-green-400">
        <Users className="w-3 h-3 mr-1" />
        <span className="font-medium">{item.clients_count || 0}</span>
      </div>
      <div className="flex items-center text-purple-600 dark:text-purple-400">
        <UserCheck className="w-3 h-3 mr-1" />
        <span className="font-medium">{item.professionals_count || 0}</span>
      </div>
      <div className="flex items-center text-gray-600 dark:text-gray-400">
        <User className="w-3 h-3 mr-1" />
        <span className="font-medium">{item.users_count || 0}</span>
      </div>
    </div>
  ),
},

// =================== OPÇÃO 4: TEXTO ABREVIADO (SUA SUGESTÃO) ===================
// Formato abreviado: "Est: 99 • Cli: 999" em 2 linhas
{
  key: "establishments_count",
  label: "Entidades",
  type: "custom",
  render: (value, item) => (
    <div className="text-sm space-y-1 font-mono">
      <div className="text-gray-700 dark:text-gray-300">
        <span className="text-blue-600 font-semibold">Est:</span> {item.establishments_count || 0} •{" "}
        <span className="text-green-600 font-semibold">Cli:</span> {item.clients_count || 0}
      </div>
      <div className="text-gray-700 dark:text-gray-300">
        <span className="text-purple-600 font-semibold">Pro:</span> {item.professionals_count || 0} •{" "}
        <span className="text-gray-600 font-semibold">Usr:</span> {item.users_count || 0}
      </div>
    </div>
  ),
},

// ====================== OPÇÃO 5: SUPER COMPACTO UMA LINHA ======================
// Máxima compactação em uma só linha
{
  key: "establishments_count",
  label: "Entidades",
  type: "custom",
  render: (value, item) => (
    <div className="text-xs font-mono text-gray-700 dark:text-gray-300">
      <span className="text-blue-600">E{item.establishments_count || 0}</span> •{" "}
      <span className="text-green-600">C{item.clients_count || 0}</span> •{" "}
      <span className="text-purple-600">P{item.professionals_count || 0}</span> •{" "}
      <span className="text-gray-600">U{item.users_count || 0}</span>
    </div>
  ),
},
