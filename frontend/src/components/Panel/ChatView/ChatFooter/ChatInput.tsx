import { Box, TextField, IconButton } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import React from "react";

export default function ChatInput({
  handleSendMessage,
  inputValue,
  setInputValue,
}: {
  handleSendMessage: (prompt: string) => void;
  inputValue: string;
  setInputValue: (s: string) => void;
}) {
  const onSubmitHandler = (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (inputValue.trim()) {
      handleSendMessage(inputValue);
    }
  };

  return (
    <Box
      component="form"
      onSubmit={onSubmitHandler}
      sx={{
        p: 2,
        bgcolor: "background.paper",
        transition: (theme) => theme.transitions.create("background-color"),
      }}
    >
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        <TextField
          fullWidth
          size="small"
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          placeholder="Write your message..."
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: 3,
              bgcolor: (theme) =>
                theme.palette.mode === "light" ? "grey.50" : "grey.900",
            },
          }}
        />
        <IconButton
          type="submit"
          color="primary"
          sx={{
            bgcolor: "primary.main",
            color: "primary.contrastText",
            borderRadius: 3,
            p: 1.3,
            "&:hover": {
              bgcolor: "primary.dark",
            },
          }}
          aria-label="Send message"
        >
          <SendIcon fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  );
}
