import { Box, Typography, List, Button, Divider } from "@mui/material";
import type { Chat } from "../../../types/types";
import { customScrollbar } from "../../../theme/scrollBarStyles";
import ChatHistoryItem from "./ChatHistoryItem";

interface ChatHistoryProps {
  open: boolean;
  sessions: Chat[];
  activeSessionId?: string | null;
  onSelectSession: (session: Chat) => void;
  onNewChat: () => void;
}

function formatRelativeDate(isoString: string) {
  const date = new Date(isoString);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  if (isToday) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  return date.toLocaleDateString([], { day: "2-digit", month: "2-digit" });
}

export default function ChatHistory({
  open,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
}: ChatHistoryProps) {
  const sortedSessions = [...sessions].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  );

  return (
    <Box
      sx={{
        position: "absolute",
        inset: 0,
        bgcolor: "background.paper",
        display: "flex",
        flexDirection: "column",
        transform: open ? "translateX(0)" : "translateX(-100%)",
        transition: (theme) =>
          theme.transitions.create("transform", {
            duration: theme.transitions.duration.short,
          }),
        zIndex: 2,
      }}
    >
      <Box sx={{ px: 1.5, pt: 1.5, pb: 1 }}>
        <Button
          fullWidth
          size="medium"
          variant="contained"
          onClick={onNewChat}
          sx={{ textTransform: "none", borderRadius: 2 }}
        >
          New Chat
        </Button>
      </Box>

      <Divider />

      <List
        dense
        sx={(theme) => ({
          flex: 1,
          overflowY: "auto",
          scrollbarGutter: "stable",
          py: 0.5,
          ...customScrollbar(theme),
        })}
      >
        {sortedSessions.length === 0 ? (
          <Box sx={{ px: 2, py: 3, textAlign: "center" }}>
            <Typography variant="caption" color="text.secondary">
              No saved conversations
            </Typography>
          </Box>
        ) : (
          sortedSessions.map((session, idx) => {
            const isActive = session.id === activeSessionId;

            return (
              <ChatHistoryItem
                key={idx}
                session={session}
                formattedDate={formatRelativeDate(session.updatedAt)}
                isActive={isActive}
                onSelectSession={onSelectSession}
              />
            );
          })
        )}
      </List>
    </Box>
  );
}
