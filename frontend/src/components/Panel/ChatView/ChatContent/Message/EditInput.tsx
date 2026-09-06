import { Box, Button, Stack, TextField } from "@mui/material";
import React from "react";

interface EditInputProps {
  editValue: string;
  setEditValue: (v: string) => void;
  handleConfirmEdit: () => void;
  handleCancelEdit: () => void;
}

export default function EditInput({
  editValue,
  handleCancelEdit,
  handleConfirmEdit,
  setEditValue,
}: EditInputProps) {
  return (
    <Box sx={{ width: "100%", maxWidth: "80%" }}>
      <TextField
        title="Edit Input"
        inputRef={(el) => {
          if (el) el.setAttribute("data-cy", "edit-input");
        }}
        fullWidth
        multiline
        autoFocus
        size="small"
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleConfirmEdit();
          }
          if (e.key === "Escape") {
            handleCancelEdit();
          }
        }}
        sx={{
          "& .MuiOutlinedInput-root": {
            borderRadius: 2,
            fontSize: "0.875rem",
            bgcolor: "background.paper",
          },
        }}
      />
      <Stack
        direction="row"
        spacing={1}
        sx={{
          mt: 1,
          justifyContent: "flex-end",
        }}
      >
        <Button
          aria-label="Cancel Edit Button"
          data-cy="cancel-edit-button"
          size="small"
          onClick={handleCancelEdit}
          sx={{ textTransform: "none", borderRadius: 2 }}
        >
          Cancel
        </Button>
        <Button
          title="Confirm Edit Button"
          data-cy="confirm-edit-button"
          size="small"
          variant="contained"
          onClick={handleConfirmEdit}
          disabled={!editValue.trim()}
          sx={{ textTransform: "none", borderRadius: 2 }}
        >
          Confirm
        </Button>
      </Stack>
    </Box>
  );
}
