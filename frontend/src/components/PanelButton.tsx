import { Fab } from "@mui/material";
import SmartToyIcon from "@mui/icons-material/SmartToy";

interface PanelButtonProps {
  toggleChat: () => void;
  isOpen: boolean;
}

export default function PanelButton({ toggleChat, isOpen }: PanelButtonProps) {
  if (isOpen) return null;

  return (
    <Fab
      onClick={toggleChat}
      title="Open Chatbot"
      color="primary"
      sx={{
        position: "fixed",
        bottom: 24,
        right: 24,
        zIndex: (theme) => theme.zIndex.tooltip,
        height: 64,
        width: 64,
        boxShadow: (theme) =>
          theme.palette.mode === "light"
            ? theme.shadows[6]
            : "0 10px 15px -3px rgba(15, 23, 42, 0.8)",
        transition: (theme) =>
          theme.transitions.create([
            "transform",
            "background-color",
            "box-shadow",
          ]),
        "&:hover": {
          transform: "scale(1.05)",
          boxShadow: (theme) => theme.shadows[10],
        },
        "&:focus-visible": {
          outline: "2px solid",
          outlineColor: "primary.main",
          outlineOffset: "2px",
        },
      }}
    >
      <SmartToyIcon sx={{ fontSize: 32 }} />
    </Fab>
  );
}
