import "@fontsource-variable/bricolage-grotesque";
import "@fontsource/hind/400.css";
import "@fontsource/hind/600.css";
import "@fontsource/hind/devanagari-400.css";
import "@fontsource/hind/devanagari-600.css";
import "@fontsource/jetbrains-mono/400.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles/tokens.css";
import "./styles/app.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
