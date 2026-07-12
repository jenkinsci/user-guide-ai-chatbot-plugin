import React, { useEffect, useState } from "react";
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
import { apiCall } from "../../../../api/api";

interface ChatToolsProps {
  activeChatId: number | null;
  currentPageName: string;
  onUploadContext: () => Promise<boolean>;
}

const formatDateToTwoDigit = (date: Date) => {
  const timeString = date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  return timeString;
};

export function ChatTools({
  activeChatId,
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
      const timeString = formatDateToTwoDigit(now);

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

  useEffect(() => {
    const fetchLastUploadDate = async () => {
      setUploadedTime(null);
      if (!activeChatId) return;

      try {
        const response = await apiCall({
          method: "GET",
          path: `context/${activeChatId}/last-upload`,
        });
        const data = await response.json();

        const lastUploadAt = data["last_upload_at"];

        if (!lastUploadAt) return;

        setUploadedTime(formatDateToTwoDigit(new Date(lastUploadAt)));
      } catch (e) {
        console.log(e);
      }
    };

    fetchLastUploadDate();
  }, [activeChatId]);

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
