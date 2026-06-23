import { useState, type SubmitEventHandler } from "react";
import { Box, Drawer } from "@mui/material";
import ChatFooter from "./ChatFooter/ChatFooter";
import Header from "./Header/Header";
import { ChatPlaceholder } from "./ChatPlaceholder/ChatPlaceholder";
import type { ChatMessage, Chat } from "../../types/types";
import ChatContent from "./ChatContent/ChatContent";
import ChatHistory from "./ChatHistory/ChatHistory";
import { DUMMY_MESSAGES, DUMMY_SESSIONS } from "../../data/dummyData";

interface ChatSidePanelProps {
  isOpen: boolean;
  toggleChat: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}


export default function SidePanel({
  isOpen,
  toggleChat,
  isDarkMode,
  onToggleDarkMode,
}: ChatSidePanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isBotTyping, setIsBotTyping] = useState<boolean>(false);
  const [inputValue, setInputValue] = useState<string>("");

  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [sessions, setSessions] = useState<Chat[]>(DUMMY_SESSIONS);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  const [sessionMessages, setSessionMessages] =
    useState<Record<string, ChatMessage[]>>(DUMMY_MESSAGES);

  const onSendMessage: SubmitEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    if (!inputValue.trim()) return;
    sendMessage(inputValue);
  };

  const sendMessage = (text: string) => {
    let sessionId = activeSessionId;

    if (!sessionId) {
      sessionId = crypto.randomUUID();
      const newSession: Chat = {
        id: sessionId,
        title: text.slice(0, 40),
        updatedAt: new Date().toISOString(),
      };
      setSessions((prev) => [...prev, newSession]);
      setActiveSessionId(sessionId);
    } else {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? { ...s, updatedAt: new Date().toISOString() }
            : s,
        ),
      );
    }

    const userMessage: ChatMessage = {
      id: Date.now(),
      sender: "user",
      text: text,
      createdAt: new Date().toISOString(),
      updatedAt: null,
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setSessionMessages((prev) => ({ ...prev, [sessionId!]: updatedMessages }));
    setInputValue("");
    setIsBotTyping(true);

    setTimeout(() => {
      const botMessage: ChatMessage = {
        id: Date.now() + 1,
        sender: "bot",
        text: "I received your message. This is an automated response.",
        createdAt: new Date().toISOString(),
        updatedAt: null,
      };
      setMessages((prevMessages) => {
        const next = [...prevMessages, botMessage];
        setSessionMessages((prevStore) => ({
          ...prevStore,
          [sessionId!]: next,
        }));
        return next;
      });
      setIsBotTyping(false);
    }, 1000);
  };

  const onSuggestionClick = (text: string) => {
    sendMessage(text);
  };

  const onEditMessageConfirm = (message: ChatMessage, newText: string) => {
    const index = messages.findIndex((m) => m.id === message.id);
    if (index === -1) return;

    const updatedMessage: ChatMessage = {
      ...messages[index],
      text: newText,
      updatedAt: new Date().toISOString(),
    };

    const truncated = [...messages.slice(0, index), updatedMessage];
    setMessages(truncated);
    if (activeSessionId) {
      setSessionMessages((prev) => ({ ...prev, [activeSessionId]: truncated }));
    }
    regenerateBotResponse(newText);
  };

  const onRetryMessage = (botMessage: ChatMessage) => {
    const index = messages.findIndex((m) => m.id === botMessage.id);
    if (index === -1) return;

    const truncated = messages.slice(0, index);
    setMessages(truncated);
    if (activeSessionId) {
      setSessionMessages((prev) => ({ ...prev, [activeSessionId]: truncated }));
    }

    const lastUserMessage = [...truncated]
      .reverse()
      .find((m) => m.sender === "user");
    if (lastUserMessage) {
      regenerateBotResponse(lastUserMessage.text);
    }
  };

  const regenerateBotResponse = (promptText: string) => {
    setIsBotTyping(true);
    setTimeout(() => {
      const botMessage: ChatMessage = {
        id: Date.now(),
        sender: "bot",
        text: `New response to: "${promptText}"`,
        createdAt: new Date().toISOString(),
        updatedAt: null,
      };
      setMessages((prevMessages) => {
        const next = [...prevMessages, botMessage];
        if (activeSessionId) {
          setSessionMessages((prevStore) => ({
            ...prevStore,
            [activeSessionId]: next,
          }));
        }
        return next;
      });
      setIsBotTyping(false);
    }, 1000);
  };

  const handleNewChat = () => {
    setMessages([]);
    setActiveSessionId(null);
    setInputValue("");
    setIsHistoryOpen(false);
  };

  const handleSelectSession = (session: Chat) => {
    setActiveSessionId(session.id);
    setMessages(sessionMessages[session.id] ?? []);
    setInputValue("");
    setIsHistoryOpen(false);
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
        toggleHistory={() => setIsHistoryOpen((prev) => !prev)}
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
        {messages.length === 0 ? (
          <ChatPlaceholder onSuggestionClick={onSuggestionClick} />
        ) : (
          <ChatContent
            messages={messages}
            isBotTyping={isBotTyping}
            onEditMessageConfirm={onEditMessageConfirm}
            onRetryMessage={onRetryMessage}
          />
        )}
        <ChatFooter
          handleSendMessage={onSendMessage}
          inputValue={inputValue}
          setInputValue={setInputValue}
        />

        <ChatHistory
          open={isHistoryOpen}
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
        />
      </Box>
    </Drawer>
  );
}
