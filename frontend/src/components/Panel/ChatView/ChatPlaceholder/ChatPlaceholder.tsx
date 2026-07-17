import { Box, Typography, Stack } from "@mui/material";
import { PromptSuggested } from "./PromptSuggested";
import { useMemo } from "react";

export function ChatPlaceholder({
  onSuggestionClick,
}: {
  onSuggestionClick: (prompt: string) => void;
}) {
  const pluginBaseUrl = useMemo(() => {
    const rootElement = document.getElementById("jenkins-ai-chatbot-root");
    return rootElement?.getAttribute("data-plugin-base-url") || "";
  }, []);

  let absoluteLogoUrl = "images/jenkins_logo.png";
  if (pluginBaseUrl) {
    absoluteLogoUrl = `${pluginBaseUrl}/${absoluteLogoUrl}`;
  }

  const suggestedPrompts: string[] = [
    "Do you know why my build isn't working?",
    "How can I install a new plugin?",
    "How can I create a new Pipeline?",
    "What's the difference between a Jenkins pipeline and a project?",
  ];

  return (
    <Box
      sx={{
        display: "flex",
        height: "100%",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        p: 3,
        textAlign: "center",
      }}
    >
      <Box
        component="img"
        src={absoluteLogoUrl}
        alt="Jenkins Logo"
        sx={{
          mb: 3,
          width: 140,
          objectFit: "contain",
          filter: "drop-shadow(0 4px 3px rgba(0,0,0,0.07))",
        }}
      />

      <Typography
        variant="h5"
        sx={{ mb: 0.5, fontWeight: 700, color: "text.primary" }}
      >
        Need help?
      </Typography>

      <Typography
        variant="body2"
        sx={{ mb: 2, fontWeight: 500, color: "text.secondary" }}
      >
        Try with:
      </Typography>

      <Stack spacing={1.5} sx={{ width: "100%", maxWidth: 320 }}>
        {suggestedPrompts.map((prompt, index) => (
          <PromptSuggested
            prompt={prompt}
            key={index}
            onClick={onSuggestionClick}
          />
        ))}
      </Stack>
    </Box>
  );
}
