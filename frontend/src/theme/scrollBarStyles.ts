import type { Theme } from "@mui/material/styles";

export const customScrollbar = (theme: Theme) => ({
  "&::-webkit-scrollbar": {
    width: 8,
  },
  "&::-webkit-scrollbar-track": {
    background: "transparent",
  },
  "&::-webkit-scrollbar-thumb": {
    backgroundColor:
      theme.palette.mode === "light"
        ? theme.palette.grey[300]
        : theme.palette.grey[700],
    borderRadius: 999,
    border: "2px solid transparent",
    backgroundClip: "padding-box",
  },
  "&::-webkit-scrollbar-thumb:hover": {
    backgroundColor:
      theme.palette.mode === "light"
        ? theme.palette.grey[400]
        : theme.palette.grey[600],
  },
  // Firefox
  scrollbarWidth: "thin" as const,
  scrollbarColor:
    theme.palette.mode === "light"
      ? `${theme.palette.grey[300]} transparent`
      : `${theme.palette.grey[700]} transparent`,
});
