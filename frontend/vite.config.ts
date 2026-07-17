import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  base: '/plugin/user-guide-ai-chatbot/',
  plugins: [react()],
  build: {
    outDir: "../src/main/webapp",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: `js/bundle.js`,
        chunkFileNames: `js/[name].js`,
        assetFileNames: `css/[name].[ext]`,
      },
    },
  },
});
