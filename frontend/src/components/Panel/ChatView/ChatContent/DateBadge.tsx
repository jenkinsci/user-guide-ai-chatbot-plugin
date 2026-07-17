import { Box, Fade, Typography } from "@mui/material";
import React from "react";

export default function DateBadge({
  isDateBadgeVisible,
  visibleDate,
}: {
  visibleDate: string | null;
  isDateBadgeVisible: boolean;
}) {
  return (
    <Box
      sx={{
        position: "absolute",
        top: 16,
        left: 0,
        right: 0,
        zIndex: 10,
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
      }}
    >
      <Fade in={isDateBadgeVisible}>
        <Box
          sx={{
            bgcolor: "rgba(0, 0, 0, 0.5)",
            color: "white",
            px: 2,
            py: 0.5,
            borderRadius: 4,
            backdropFilter: "blur(6px)",
            boxShadow: 1,
          }}
        >
          <Typography variant="caption" sx={{ fontWeight: "medium" }}>
            {visibleDate}
          </Typography>
        </Box>
      </Fade>
    </Box>
  );
}
