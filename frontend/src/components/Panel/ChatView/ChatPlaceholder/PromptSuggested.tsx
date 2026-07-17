import { Button } from "@mui/material";

export function PromptSuggested({
  prompt,
  onClick,
}: {
  prompt: string;
  onClick: (text: string) => void;
}) {
  return (
    <Button
      onClick={() => onClick(prompt)}
      fullWidth
      sx={{
        borderRadius: 999,
        border: 1,
        borderColor: "divider",
        bgcolor: (theme) =>
          theme.palette.mode === "light" ? "grey.50" : "grey.800",
        color: "text.secondary",
        fontSize: "0.75rem",
        fontWeight: 700,
        textTransform: "none",
        py: 1,
        px: 2,
        boxShadow: 1,
        transition: (theme) =>
          theme.transitions.create(["background-color", "color"]),
        "&:hover": {
          bgcolor: (theme) =>
            theme.palette.mode === "light" ? "grey.100" : "grey.700",
          color: (theme) =>
            theme.palette.mode === "light" ? "primary.main" : "warning.light",
        },
        "&:focus-visible": {
          outline: "2px solid",
          outlineColor: "primary.main",
          outlineOffset: "1px",
        },
      }}
    >
      {prompt}
    </Button>
  );
}
