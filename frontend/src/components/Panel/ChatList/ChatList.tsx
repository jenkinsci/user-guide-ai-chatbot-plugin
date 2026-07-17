import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Typography,
  List,
  Button,
  Divider,
  CircularProgress,
} from "@mui/material";
import { ChatEntity } from "../../../models/models";
import { customScrollbar } from "../../../theme/scrollBarStyles";
import ChatListItem from "./ChatListItem";
import { apiCall } from "../../../api/api";
import ErrorBanner from "../../ErrorBanner";

interface ChatListProps {
  open: boolean;
  activeChatId?: number | null;
  onSelectChat: (session: ChatEntity) => void;
  onNewChat: () => void;
  chats: ChatEntity[];
  setChats: React.Dispatch<React.SetStateAction<ChatEntity[]>>;
}

function formatRelativeDate(date: Date) {
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  if (isToday) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  return date.toLocaleDateString([], { day: "2-digit", month: "2-digit" });
}

export default function ChatList({
  open,
  activeChatId,
  onSelectChat,
  onNewChat,
  chats,
  setChats,
}: ChatListProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [hasInitialLoadFailed, setHasInitialLoadFailed] = useState(false);

  const LIMIT = 20;

  const handleCloseError = () => {
    setErrorMessage(null);
  };

  const fetchChats = useCallback(
    async (currentOffset: number, isRetry = false) => {
      // Prevent fetching if already loading, if no more data, OR if it previously failed (unless it's an explicit retry)
      if (isLoading || !hasMore || (hasInitialLoadFailed && !isRetry)) return;

      setIsLoading(true);

      if (isRetry) {
        setHasInitialLoadFailed(false);
        setErrorMessage(null);
      }

      try {
        const response = await apiCall({
          method: "GET",
          path: `chats?limit=${LIMIT}&offset=${currentOffset}`,
        });

        if (!response.ok) {
          throw new Error(`HTTP Error: ${response.status}`);
        }

        const data = await response.json();

        const newChats: ChatEntity[] = data["items"].map((el: any) => {
          return new ChatEntity(el);
        });

        if (newChats.length < LIMIT) {
          setHasMore(false);
        }

        setChats((prevSessions) =>
          currentOffset === 0 ? newChats : [...prevSessions, ...newChats],
        );
        setOffset(currentOffset + LIMIT);
      } catch (error) {
        console.error("Failed to load chat history:", error);
        setErrorMessage("Failed to load chat history. Please try again later.");

        // Mark the load as failed to prevent the useEffect from spamming requests
        if (currentOffset === 0) {
          setHasInitialLoadFailed(true);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, hasMore, hasInitialLoadFailed, setChats],
  );

  useEffect(() => {
    if (open && chats.length === 0 && hasMore && !hasInitialLoadFailed) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchChats(0);
    }
  }, [open, chats.length, hasMore, hasInitialLoadFailed, fetchChats]);

  const handleScroll = (event: React.UIEvent<HTMLUListElement>) => {
    const listElement = event.currentTarget;

    const isNearBottom =
      listElement.scrollHeight - listElement.scrollTop <=
      listElement.clientHeight + 50;

    if (isNearBottom && hasMore && !isLoading && !hasInitialLoadFailed) {
      fetchChats(offset);
    }
  };

  const sortedChats = [...chats].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  );

  const onDeleteChat = async (chatId: number) => {
    const chatToRestore = chats.find((chat) => chat.id === chatId);
    if (!chatToRestore) return;

    setChats((prevChats) => prevChats.filter((chat) => chat.id !== chatId));

    try {
      await apiCall({
        method: "DELETE",
        path: `chats/${chatId}`,
      });
    } catch (error) {
      console.error(`Failed to delete chat with ID ${chatId}:`, error);
      setChats((prevChats) => [...prevChats, chatToRestore]);
      setErrorMessage("Unable to delete the chat. It has been restored.");
    }
  };

  const onEditChatTitle = async (chatId: number, newTitle: string) => {
    const originalChat = chats.find((chat) => chat.id === chatId);
    if (!originalChat) return;

    setChats((prevChats) =>
      prevChats.map((chat) => {
        if (chat.id === chatId) {
          return new ChatEntity({
            id: chat.id,
            user_id: chat.userId,
            title: newTitle,
            created_at: chat.createdAt.toISOString(),
            updated_at: new Date().toISOString(),
          });
        }
        return chat;
      }),
    );

    try {
      await apiCall({
        method: "PUT",
        path: `chats/${chatId}/title`,
        payload: { new_title: newTitle },
      });
    } catch (error) {
      console.error(`Failed to update title for chat ID ${chatId}:`, error);
      setChats((prevChats) =>
        prevChats.map((chat) => {
          if (chat.id === chatId) {
            return new ChatEntity({
              id: originalChat.id,
              user_id: originalChat.userId,
              title: originalChat.title,
              created_at: originalChat.createdAt.toISOString(),
              updated_at: originalChat.updatedAt.toISOString(),
            });
          }
          return chat;
        }),
      );
      setErrorMessage(
        "Failed to rename the chat. The original title was restored.",
      );
    }
  };

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
        onScroll={handleScroll}
        sx={(theme) => ({
          flex: 1,
          overflowY: "auto",
          scrollbarGutter: "stable",
          py: 0.5,
          ...customScrollbar(theme),
        })}
      >
        {/* NEW: Render a retry UI if the initial fetch failed entirely */}
        {hasInitialLoadFailed && sortedChats.length === 0 ? (
          <Box
            sx={{
              px: 2,
              py: 3,
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              gap: 2,
              alignItems: "center",
            }}
          >
            <Typography variant="caption" color="error">
              Unable to load history.
            </Typography>
            <Button
              size="small"
              variant="outlined"
              onClick={() => fetchChats(0, true)}
              disabled={isLoading}
            >
              Retry
            </Button>
          </Box>
        ) : sortedChats.length === 0 && !isLoading ? (
          <Box sx={{ px: 2, py: 3, textAlign: "center" }}>
            <Typography variant="caption" color="text.secondary">
              No saved conversations
            </Typography>
          </Box>
        ) : (
          sortedChats.map((chat) => {
            const isActive = chat.id === activeChatId;

            return (
              <ChatListItem
                key={chat.id}
                chat={chat}
                formattedDate={formatRelativeDate(chat.updatedAt)}
                isActive={isActive}
                onSelectChat={onSelectChat}
                onDeleteChat={onDeleteChat}
                onEditChatTitle={onEditChatTitle}
              />
            );
          })
        )}

        {isLoading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
            <CircularProgress size={20} color="inherit" />
          </Box>
        )}
      </List>

      <ErrorBanner message={errorMessage} handleCloseError={handleCloseError} />
    </Box>
  );
}
