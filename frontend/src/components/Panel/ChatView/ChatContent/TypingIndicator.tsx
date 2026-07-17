import { Box, Typography, keyframes } from "@mui/material";

const bounce = keyframes`
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  40% {
    transform: translateY(-6px);
    opacity: 1;
  }
`;

export default function TypingIndicator() {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
      }}
    >
      <Typography
        variant="caption"
        sx={{
          mb: 0.5,
          ml: 0.5,
          fontWeight: 300,
          color: "text.secondary",
        }}
      >
        Analyzing...
      </Typography>

      <Box
        sx={(theme) => ({
          display: "flex",
          alignItems: "center",
          gap: 0.6,
          width: "fit-content",
          px: 2,
          py: 1.5,
          borderRadius: 2,
          borderTopLeftRadius: 0,
          bgcolor: "background.paper",
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: theme.shadows[1],
        })}
      >
        {[0, 1, 2].map((i) => (
          <Box
            key={i}
            sx={(theme) => ({
              width: 6,
              height: 6,
              borderRadius: "50%",
              bgcolor: theme.palette.mode === "light" ? "grey.500" : "grey.400",
              animation: `${bounce} 1.4s ease-in-out infinite`,
              animationDelay: `${i * 0.16}s`,
            })}
          />
        ))}
      </Box>
    </Box>
  );
}
