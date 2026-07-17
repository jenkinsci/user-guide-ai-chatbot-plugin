import { Box, Stack } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import CloseIcon from "@mui/icons-material/Close";
import { RoundedButton } from "../../RoundedButton";

export default function Header({
  onToggleDarkMode,
  isDarkMode,
  toggleChat,
  toggleHistory,
}: {
  onToggleDarkMode: () => void;
  isDarkMode: boolean;
  toggleChat: () => void;
  toggleHistory: () => void;
}) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: 1,
        borderColor: "divider",
        p: 2,
      }}
    >
      <Box>
        <RoundedButton onClick={toggleHistory} title="Chat List">
          <MenuIcon fontSize="small" />
        </RoundedButton>
      </Box>

      <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
        <RoundedButton onClick={onToggleDarkMode} title="Toggle Theme">
          {isDarkMode ? (
            <DarkModeIcon fontSize="small" sx={{ color: "#fbbf24" }} />
          ) : (
            <LightModeIcon fontSize="small" />
          )}
        </RoundedButton>

        <RoundedButton onClick={toggleChat} title="Close Panel">
          <CloseIcon fontSize="small" />
        </RoundedButton>
      </Stack>
    </Box>
  );
}
