import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Non-default dev port on purpose: usual Vite default is 5173, CMS already uses 5180.
export default defineConfig({
  plugins: [react()],
  server: { port: 5190, strictPort: true },
  preview: { port: 5190, strictPort: true },
});
