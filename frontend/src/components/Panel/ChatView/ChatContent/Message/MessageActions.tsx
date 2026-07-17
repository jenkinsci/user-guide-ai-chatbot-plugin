import { Box, IconButton, Tooltip } from "@mui/material";
import ReplayIcon from "@mui/icons-material/Replay";
import EditIcon from "@mui/icons-material/Edit";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";

interface MessageActionsProps {
  isUser: boolean;
  copied: boolean;
  handleStartEdit: () => void;
  handleCopy: () => void;
  onRetry: () => void;
}

export default function MessageActions({
  copied,
  handleCopy,
  handleStartEdit,
  isUser,
  onRetry,
}: MessageActionsProps) {
  return isUser ? (
    <Box
      className="message-actions"
      sx={{
        display: "flex",
        gap: 0.25,
        opacity: 0,
        transition: (theme) => theme.transitions.create("opacity"),
        ".message-row:hover &": {
          opacity: 1,
        },
      }}
    >
      <Tooltip title="Edit">
        <IconButton size="small" onClick={handleStartEdit}>
          <EditIcon sx={{ fontSize: 15 }} />
        </IconButton>
      </Tooltip>
      <Tooltip title={copied ? "Copied!" : "Copy"}>
        <IconButton size="small" onClick={handleCopy}>
          {copied ? (
            <CheckIcon sx={{ fontSize: 15 }} />
          ) : (
            <ContentCopyIcon sx={{ fontSize: 15 }} />
          )}
        </IconButton>
      </Tooltip>
    </Box>
  ) : (
    <Box sx={{ display: "flex", gap: 0.25 }}>
      <Tooltip title={copied ? "Copied!" : "Copy"}>
        <IconButton size="small" onClick={handleCopy}>
          {copied ? (
            <CheckIcon sx={{ fontSize: 15 }} />
          ) : (
            <ContentCopyIcon sx={{ fontSize: 15 }} />
          )}
        </IconButton>
      </Tooltip>
      <Tooltip title="Retry">
        <IconButton size="small" onClick={() => onRetry()}>
          <ReplayIcon sx={{ fontSize: 15 }} />
        </IconButton>
      </Tooltip>
    </Box>
  );
}
