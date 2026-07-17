import { useState } from "react";
import { Box, Drawer } from "@mui/material";
import Header from "./Header/Header";
import type { ChatEntity } from "../../models/models";
import ChatList from "./ChatList/ChatList";
import ChatView from "./ChatView/ChatView";

interface ChatPanelProps {
  isOpen: boolean;
  toggleChat: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

export default function Panel({
  isOpen,
  toggleChat,
  isDarkMode,
  onToggleDarkMode,
}: ChatPanelProps) {
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [chats, setChats] = useState<ChatEntity[]>([]);
  const [isListOpen, setIsListOpen] = useState(false);

  const onCreateChat = (chat: ChatEntity) => {
    setChats((prev) => [chat, ...prev]);
    setActiveChatId(chat.id);
  };

  const handleNewChat = () => {
    setActiveChatId(null);
    setIsListOpen(false);
  };

  const handleSelectChat = (chat: ChatEntity) => {
    console.log("SELECTED CHAT: " + chat.id);
    setActiveChatId(chat.id);
    setIsListOpen(false);
  };

  return (
    <Drawer
      anchor="right"
      open={isOpen}
      onClose={toggleChat}
      variant="persistent"
      sx={{
        "& .MuiDrawer-paper": {
          width: { xs: 320, sm: 384 },
          borderLeft: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
          boxShadow: 24,
          transition: (theme) => theme.transitions.create("background-color"),
          display: "flex",
          flexDirection: "column",
        },
      }}
    >
      <Header
        isDarkMode={isDarkMode}
        toggleChat={toggleChat}
        onToggleDarkMode={onToggleDarkMode}
        toggleHistory={() => setIsListOpen((prev) => !prev)}
      />
      <Box
        sx={{
          position: "relative",
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
        }}
      >
        <ChatView activeChatId={activeChatId} onCreateChat={onCreateChat} />
        <ChatList
          chats={chats}
          setChats={setChats}
          open={isListOpen}
          activeChatId={activeChatId}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
        />
      </Box>
    </Drawer>
  );
}
