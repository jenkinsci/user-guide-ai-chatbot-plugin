import { useState } from "react";
import { Box, IconButton, Tooltip } from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";
import { copyText } from "./copyText";

interface CodeBlockProps {
  code: string;
  language?: string;
}

export default function CodeBlock({ code, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (await copyText(code)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <Box
      sx={(theme) => ({
        my: 1,
        borderRadius: 1,
        border: `1px solid ${theme.palette.divider}`,
        overflow: "hidden",
      })}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          bgcolor: "action.hover",
          px: 1,
        }}
      >
        <Box
          component="span"
          sx={{ fontSize: "0.75rem", color: "text.secondary" }}
        >
          {language || "code"}
        </Box>
        <Tooltip title={copied ? "Copied!" : "Copy code"}>
          <IconButton
            data-cy="copy-code-button"
            size="small"
            onClick={handleCopy}
          >
            {copied ? (
              <CheckIcon sx={{ fontSize: 15 }} />
            ) : (
              <ContentCopyIcon sx={{ fontSize: 15 }} />
            )}
          </IconButton>
        </Tooltip>
      </Box>
      <Box
        component="pre"
        tabIndex={0}
        sx={{
          p: 1.5,
          m: 0,
          fontSize: "0.8rem",
          overflowX: "auto",
          whiteSpace: "pre",
          fontFamily: "monospace",
          color: "text.primary",
        }}
      >
        {code}
      </Box>
    </Box>
  );
}
