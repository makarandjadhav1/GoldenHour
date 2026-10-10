import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  timeout: 30000,
  use: { baseURL: "http://localhost:5173" },
  projects: [{ name: "desktop", use: { viewport: { width: 1280, height: 900 } } }, { name: "mobile", use: { viewport: { width: 390, height: 800 } } }],
  webServer: [
    { command: "uv run uvicorn app.main:app --port 8000", cwd: "../backend", url: "http://localhost:8000/v1/health", reuseExistingServer: true },
    { command: "npx vite --port 5173", url: "http://localhost:5173", reuseExistingServer: true },
  ],
});
