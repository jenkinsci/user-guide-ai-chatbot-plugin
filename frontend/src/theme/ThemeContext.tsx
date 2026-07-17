/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { ThemeProvider as MuiThemeProvider } from "@mui/material";
import ScopedCssBaseline from "@mui/material/ScopedCssBaseline";
import { buildTheme } from "./theme";

type ThemeMode = "light" | "dark";

const ColorModeContext = createContext<{
  mode: ThemeMode;
  toggleColorMode: () => void;
}>({ mode: "light", toggleColorMode: () => {} });

function getInitialThemeMode(): ThemeMode {
  const savedTheme = localStorage.getItem("theme") as ThemeMode | null;
  if (savedTheme) return savedTheme;

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function ColorModeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(getInitialThemeMode);

  useEffect(() => {
    localStorage.setItem("theme", mode);
  }, [mode]);

  const toggleColorMode = () =>
    setMode((prevMode) => (prevMode === "light" ? "dark" : "light"));

  const activeTheme = useMemo(() => buildTheme(mode), [mode]);

  return (
    <ColorModeContext.Provider value={{ mode, toggleColorMode }}>
      <MuiThemeProvider theme={activeTheme}>
        <ScopedCssBaseline enableColorScheme>{children}</ScopedCssBaseline>
      </MuiThemeProvider>
    </ColorModeContext.Provider>
  );
}

export const useColorMode = () => useContext(ColorModeContext);
