import type { ReactNode } from "react";
import { IconButton, type IconButtonProps } from "@mui/material";

interface RoundedButtonProps {
  onClick: () => void;
  children: ReactNode;
  title: string;
}

export function RoundedButton({
  onClick,
  children,
  title,
  ...rest
}: RoundedButtonProps &
  Omit<IconButtonProps, "onClick" | "title" | "children">) {
  return (
    <IconButton
      onClick={onClick}
      title={title}
      sx={{
        height: 40,
        width: 40,
        borderRadius: "50%",
        bgcolor: (theme) =>
          theme.palette.mode === "light" ? "grey.100" : "grey.800",
        color: (theme) =>
          theme.palette.mode === "light" ? "grey.600" : "grey.300",
        transition: (theme) =>
          theme.transitions.create(["background-color", "color"]),
        "&:hover": {
          bgcolor: (theme) =>
            theme.palette.mode === "light" ? "grey.200" : "grey.700",
          color: (theme) =>
            theme.palette.mode === "light" ? "grey.900" : "common.white",
        },
        "&:focus-visible": {
          outline: "2px solid",
          outlineColor: "primary.main",
          outlineOffset: "2px",
        },
      }}
      {...rest}
    >
      {children}
    </IconButton>
  );
}
