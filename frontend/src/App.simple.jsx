import React from "react";

function App() {
  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Pro Team Care</h1>
        <p className="text-lg text-gray-600">
          Sistema de Gestão - Teste Simplificado
        </p>
        <div className="mt-8">
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            onClick={() => alert("Frontend funcionando!")}
          >
            Testar Frontend
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
