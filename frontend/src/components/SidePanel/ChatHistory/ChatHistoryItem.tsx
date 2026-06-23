import { ListItemButton, ListItemText, Typography } from "@mui/material";
import type { Chat } from "../../../types/types";
import { ChatBubbleOutlineOutlined } from "@mui/icons-material";

interface ChatHistoryItemProps {
  session: Chat;
  isActive: boolean;
  onSelectSession: (session: Chat) => void;
  formattedDate: string;
}

export default function ChatHistoryItem({
  session,
  isActive,
  formattedDate,
  onSelectSession,
}: ChatHistoryItemProps) {
  return (
    <ListItemButton
      key={session.id}
      dense
      selected={isActive}
      onClick={() => onSelectSession(session)}
      sx={{
        mx: 1,
        px: 1,
        py: 0.75,
        borderRadius: 1.5,
        mb: 0.25,
        "&.Mui-selected": {
          bgcolor: (theme) =>
            theme.palette.mode === "light" ? "grey.100" : "grey.800",
        },
        "&.Mui-selected:hover": {
          bgcolor: (theme) =>
            theme.palette.mode === "light" ? "grey.200" : "grey.700",
        },
      }}
    >
      <ChatBubbleOutlineOutlined
        sx={{
          fontSize: 16,
          mr: 1,
          color: "text.secondary",
          flexShrink: 0,
        }}
      />
      <ListItemText
        primary={
          <Typography
            noWrap
            sx={{
              fontSize: "0.8rem",
              fontWeight: isActive ? 600 : 400,
              color: (theme) => `${theme.palette.text.primary} !important`,
            }}
          >
            {session.title}
          </Typography>
        }
        secondary={
          <Typography
            sx={{
              fontSize: "0.7rem",
              color: (theme) => `${theme.palette.text.secondary} !important`,
            }}
          >
            {formattedDate}
          </Typography>
        }
        disableTypography
      />
    </ListItemButton>
  );
}
