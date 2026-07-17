import React, { useState } from "react";
import {
  ListItemButton,
  ListItemText,
  Typography,
  IconButton,
  Box,
  InputBase,
} from "@mui/material";
import {
  ChatBubbleOutlineOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined,
} from "@mui/icons-material";
import type { ChatEntity } from "../../../models/models";

interface ChatListItemProps {
  chat: ChatEntity;
  isActive: boolean;
  formattedDate: string;
  onSelectChat: (session: ChatEntity) => void;
  onEditChatTitle: (chatId: number, newTitle: string) => void;
  onDeleteChat: (chatId: number) => void;
}

export default function ChatListItem({
  chat,
  isActive,
  formattedDate,
  onSelectChat,
  onEditChatTitle,
  onDeleteChat,
}: ChatListItemProps) {
  // States for inline actions
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [editTitleValue, setEditTitleValue] = useState(chat.title);

  // --- Handlers for Editing ---
  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
    setIsDeleting(false);
    setEditTitleValue(chat.title);
  };

  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(false);
    setEditTitleValue(chat.title);
  };

  const handleSaveEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (editTitleValue.trim() !== "" && editTitleValue !== chat.title) {
      onEditChatTitle(chat.id, editTitleValue.trim());
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSaveEdit(e as unknown as React.MouseEvent);
    } else if (e.key === "Escape") {
      e.preventDefault();
      handleCancelEdit(e as unknown as React.MouseEvent);
    }
  };

  // --- Handlers for Deleting ---
  const handleStartDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDeleting(true);
    setIsEditing(false);
  };

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDeleting(false);
  };

  const handleConfirmDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDeleteChat(chat.id);
    setIsDeleting(false);
  };

  const isActionActive = isEditing || isDeleting;

  return (
    <ListItemButton
      key={chat.id}
      dense
      selected={isActive}
      onClick={() => {
        // Prevent selecting the chat if the user is currently editing or deleting
        if (!isActionActive) onSelectChat(chat);
      }}
      className="chat-list-item-group"
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
        "&:hover .chat-actions, &.Mui-selected .chat-actions": {
          opacity: 1,
          pointerEvents: "auto",
        },
      }}
    >
      <ChatBubbleOutlineOutlined
        sx={{
          fontSize: 16,
          mr: 1,
          color: isDeleting ? "error.main" : "text.secondary",
          flexShrink: 0,
        }}
      />

      <Box sx={{ flex: 1, overflow: "hidden" }}>
        {isEditing ? (
          <InputBase
            value={editTitleValue}
            onChange={(e) => setEditTitleValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onClick={(e) => e.stopPropagation()}
            autoFocus
            fullWidth
            sx={{
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "text.primary",
              p: 0,
              "& input": { p: 0 },
            }}
          />
        ) : isDeleting ? (
          // Confirmation text shown during the delete state
          <Typography
            noWrap
            sx={{
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "error.main",
            }}
          >
            Confirm deletion?
          </Typography>
        ) : (
          // Default state: Title and Date
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
                {chat.title}
              </Typography>
            }
            secondary={
              <Typography
                sx={{
                  fontSize: "0.7rem",
                  color: (theme) =>
                    `${theme.palette.text.secondary} !important`,
                }}
              >
                {formattedDate}
              </Typography>
            }
            disableTypography
            sx={{ m: 0 }}
          />
        )}
      </Box>

      {/* Action Buttons Area */}
      <Box
        className="chat-actions"
        sx={{
          display: "flex",
          // Force visibility if editing or deleting
          opacity: isActionActive ? 1 : 0,
          pointerEvents: isActionActive ? "auto" : "none",
          transition: "opacity 0.2s ease-in-out",
          ml: 1,
        }}
      >
        {isEditing ? (
          <>
            <IconButton size="small" onClick={handleSaveEdit} color="success">
              <CheckOutlined fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={handleCancelEdit} color="error">
              <CloseOutlined fontSize="small" />
            </IconButton>
          </>
        ) : isDeleting ? (
          <>
            <IconButton
              size="small"
              onClick={handleConfirmDelete}
              color="error"
            >
              <CheckOutlined fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={handleCancelDelete}>
              <CloseOutlined fontSize="small" />
            </IconButton>
          </>
        ) : (
          <>
            <IconButton size="small" onClick={handleStartEdit}>
              <EditOutlined fontSize="small" sx={{ fontSize: "1.1rem" }} />
            </IconButton>
            <IconButton size="small" onClick={handleStartDelete}>
              <DeleteOutlined fontSize="small" sx={{ fontSize: "1.1rem" }} />
            </IconButton>
          </>
        )}
      </Box>
    </ListItemButton>
  );
}
