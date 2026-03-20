import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  const apiTarget = env.VITE_API_URL
    ? new URL(env.VITE_API_URL).origin
    : "http://localhost:8000";

  return {
    plugins: [react()],

    server: {
      port: parseInt(env.VITE_PORT || "5173"),
      host: true,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
        "/media": {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },

    build: {
      outDir: "dist",
      sourcemap: mode !== "production",
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ["react", "react-dom", "react-router-dom"],
            http: ["axios"],
          },
        },
      },
    },

    preview: {
      port: parseInt(env.VITE_PREVIEW_PORT || "4173"),
    },
  };
});