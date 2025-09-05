import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0", // Permitir acesso da rede local
    port: 3000,
    cors: {
      origin: ["http://192.168.11.83:3000", "http://localhost:3000", "http://192.168.11.83:3001", "http://localhost:3001"],
      credentials: true,
      methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
      allowedHeaders: ["Content-Type", "Authorization", "X-Requested-With"],
    },
    fs: {
      // Resolver problemas de source map do React DevTools
      allow: ['..']
    },
    proxy: {
      "/api": {
        target: "http://192.168.11.83:8000", // Backend API
        changeOrigin: true,
        secure: false,
        // Configurar headers CORS diretamente
        configure: (proxy, options) => {
          proxy.on("proxyRes", (proxyRes, req, res) => {
            // Adicionar headers CORS necessários
            res.setHeader(
              "Access-Control-Allow-Origin",
              "http://192.168.11.83:3000"
            );
            res.setHeader("Access-Control-Allow-Credentials", "true");
            res.setHeader(
              "Access-Control-Allow-Methods",
              "GET, POST, PUT, DELETE, OPTIONS"
            );
            res.setHeader(
              "Access-Control-Allow-Headers",
              "Content-Type, Authorization, X-Requested-With"
            );
          });
        },
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  css: {
    devSourcemap: false // Resolver erro de source map em desenvolvimento
  },
});
