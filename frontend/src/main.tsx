import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { ColorModeProvider } from "./theme/ThemeContext.tsx";

createRoot(
  document.getElementById("jenkins-ai-chatbot-root") ||
    document.getElementById("root")!,
).render(
  <StrictMode>
    <ColorModeProvider>
      <App />
    </ColorModeProvider>
  </StrictMode>,
);
