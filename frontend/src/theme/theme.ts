// src/theme/theme.ts
import { createTheme, type ThemeOptions } from "@mui/material/styles";

const getDesignTokens = (mode: "light" | "dark"): ThemeOptions => {
  return {
    palette: {
      mode,
      ...(mode === "light"
        ? {
            background: {
              default: "#ffffff",
              paper: "#ffffff",
            },
            text: {
              primary: "#1e293b",
            },
          }
        : {
            background: {
              default: "#0f172a",
              paper: "#1e293b",
            },
            text: {
              primary: "#f1f5f9",
            },
          }),
      primary: {
        main: "#2563eb",
      },
    },
    shape: {
      borderRadius: 16,
    },
  };
};

export const buildTheme = (mode: "light" | "dark") =>
  createTheme(getDesignTokens(mode));
