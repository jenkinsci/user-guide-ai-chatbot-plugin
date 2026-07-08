import React, { useState } from "react";
import {
  Box,
  Typography,
  Chip,
  CircularProgress,
  Tooltip,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import SyncIcon from "@mui/icons-material/Sync";

interface ChatToolsProps {
  currentPageName: string;
  onUploadContext: () => Promise<boolean>;
}

export function ChatTools({
  currentPageName,
  onUploadContext,
}: ChatToolsProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedTime, setUploadedTime] = useState<string | null>(null);
  const [showSuccessTick, setShowSuccessTick] = useState(false);

  const handleUploadClick = async () => {
    if (isUploading) return;

    setIsUploading(true);
    setShowSuccessTick(false);

    try {
      const uploaded = await onUploadContext();

      const now = new Date();
      const timeString = now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      if (uploaded) {
        setUploadedTime(timeString);
        setShowSuccessTick(true);
      }

      setTimeout(() => {
        setShowSuccessTick(false);
      }, 2000);
    } catch (error) {
      console.error("Failed to upload context:", error);
    } finally {
      setIsUploading(false);
    }
  };

  const isPersistentSavedState =
    !!uploadedTime && !isUploading && !showSuccessTick;

  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        alignItems: "center",
        justifyContent: "space-between",
        borderTopLeftRadius: 3,
        borderTopRightRadius: 3,
        borderTop: 1,
        borderColor: "divider",
        bgcolor: "background.paper",
        px: 2,
        pt: 1,
        pb: 0.5,
        boxShadow: 1,
        transition: (theme) => theme.transitions.create("background-color"),
      }}
    >
      <Typography
        variant="body2"
        sx={{
          color: (theme) => `${theme.palette.text.secondary} !important`,
        }}
      >
        Page:{" "}
        <Typography
          component="span"
          variant="body2"
          sx={{
            fontWeight: 600,
            color: (theme) => `${theme.palette.text.primary} !important`,
          }}
        >
          {currentPageName}
        </Typography>
      </Typography>

      <Tooltip
        title={
          uploadedTime
            ? "Context saved. Click again to update with the latest page state."
            : "Upload current page context to chat"
        }
        placement="top"
        arrow
      >
        <Chip
          onClick={handleUploadClick}
          disabled={isUploading}
          color={
            showSuccessTick || isPersistentSavedState ? "success" : "default"
          }
          variant={isPersistentSavedState ? "outlined" : "filled"}
          icon={
            isUploading ? (
              <CircularProgress size={16} color="inherit" />
            ) : showSuccessTick ? (
              <CheckCircleIcon fontSize="small" />
            ) : uploadedTime ? (
              <SyncIcon fontSize="small" />
            ) : (
              <UploadFileIcon fontSize="small" />
            )
          }
          label={
            isUploading
              ? "Uploading..."
              : showSuccessTick
                ? "Uploaded!"
                : uploadedTime
                  ? `Updated at ${uploadedTime}`
                  : "Upload Context"
          }
          sx={{
            fontWeight: 500,
            cursor: "pointer",
            "&:focus-visible": {
              outline: "2px solid",
              outlineColor: "primary.main",
              outlineOffset: "1px",
            },
            transition: "all 0.3s ease",
          }}
        />
      </Tooltip>
    </Box>
  );
}
