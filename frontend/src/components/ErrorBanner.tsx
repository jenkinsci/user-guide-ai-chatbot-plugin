import React from "react";
import { Alert, Snackbar } from "@mui/material";

export default function ErrorBanner({
  message,
  handleCloseError,
}: {
  message: string | null;
  handleCloseError: () => void;
}) {
  return (
    <Snackbar
      open={!!message}
      autoHideDuration={4000}
      onClose={handleCloseError}
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      sx={{ position: "absolute", width: "90%" }}
    >
      <Alert
        onClose={handleCloseError}
        severity="error"
        variant="filled"
        sx={{ width: "100%", borderRadius: 2, alignItems: "center" }}
      >
        {message}
      </Alert>
    </Snackbar>
  );
}
