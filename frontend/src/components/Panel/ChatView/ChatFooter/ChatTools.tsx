import { Box, Typography, Chip } from "@mui/material";
import AttachFileIcon from "@mui/icons-material/AttachFile";

interface ChatToolsProps {
  currentPageName: string;
  onAttachContext: () => void;
}

export function ChatTools({
  currentPageName,
  onAttachContext,
}: ChatToolsProps) {
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
        Current page:{" "}
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
      <Chip
        onClick={onAttachContext}
        title="Attach current page context to chat"
        icon={<AttachFileIcon fontSize="small" />}
        label="Attach Context"
        sx={{
          bgcolor: (theme) =>
            theme.palette.mode === "light" ? "grey.100" : "grey.800",
          color: "text.primary",
          fontWeight: 500,
          "&:hover": {
            bgcolor: (theme) =>
              theme.palette.mode === "light" ? "grey.200" : "grey.700",
          },
          "&:focus-visible": {
            outline: "2px solid",
            outlineColor: "primary.main",
            outlineOffset: "1px",
          },
        }}
      />
    </Box>
  );
}
