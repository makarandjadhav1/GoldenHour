/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/v1": "http://localhost:8000" } },
  test: { environment: "jsdom", include: ["src/**/*.test.{ts,tsx}"] },
});
