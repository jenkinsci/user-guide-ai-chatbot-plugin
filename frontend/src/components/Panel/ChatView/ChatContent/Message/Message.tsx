import { Box, Typography } from "@mui/material";
import { AnswerEntity, QuestionEntity } from "../../../../../models/models";
import EditInput from "./EditInput";
import { useState } from "react";
import MessageActions from "./MessageActions";

interface QuestionMessageProps {
  message: QuestionEntity;
  onEditConfirm: (message: QuestionEntity, newText: string) => void;
  onRetry?: never;
}

interface AnswerMessageProps {
  message: AnswerEntity;
  onRetry: () => void;
  onEditConfirm?: never;
}

export type MessageProps = QuestionMessageProps | AnswerMessageProps;

function formatTime(date: Date) {
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Message({
  message,
  onRetry,
  onEditConfirm,
}: MessageProps) {
  const isUser = message instanceof QuestionEntity;
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(message.content);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleStartEdit = () => {
    setEditValue(message.content);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditValue(message.content);
    setIsEditing(false);
  };

  const handleConfirmEdit = () => {
    const trimmed = editValue.trim();
    if (!trimmed || !onEditConfirm) return;
    onEditConfirm(message, trimmed);
    setIsEditing(false);
  };

  return (
    <Box
      className="message-row"
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
      }}
    >
      {isEditing ? (
        <EditInput
          editValue={editValue}
          handleCancelEdit={handleCancelEdit}
          handleConfirmEdit={handleConfirmEdit}
          setEditValue={setEditValue}
        />
      ) : (
        <Box
          sx={(theme) => ({
            maxWidth: "80%",
            minWidth: 0,
            px: 2,
            py: 1.25,
            fontSize: "0.875rem",
            boxShadow: theme.shadows[1],
            transition: theme.transitions.create(["background-color", "color"]),
            borderRadius: 2,
            wordBreak: "break-word",
            overflowWrap: "break-word",
            whiteSpace: "pre-wrap",
            ...(isUser
              ? {
                  bgcolor: "primary.main",
                  color: "primary.contrastText",
                  borderTopRightRadius: 0,
                }
              : {
                  bgcolor: "background.paper",
                  color: "text.primary",
                  border: `1px solid ${theme.palette.divider}`,
                  borderTopLeftRadius: 0,
                }),
          })}
        >
          {message.content}
        </Box>
      )}

      {!isEditing && (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 0.5,
            mt: 0.5,
            px: 0.5,
            flexDirection: isUser ? "row-reverse" : "row",
          }}
        >
          <Typography
            variant="caption"
            sx={{ color: "text.disabled", fontWeight: 300, userSelect: "none" }}
          >
            {formatTime(message.createdAt)}
          </Typography>

          <MessageActions
            copied={copied}
            handleCopy={handleCopy}
            handleStartEdit={handleStartEdit}
            isUser={isUser}
            onRetry={() => onRetry!()}
          />
        </Box>
      )}
    </Box>
  );
}
