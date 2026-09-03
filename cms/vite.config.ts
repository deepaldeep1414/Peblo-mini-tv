import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Non-default dev port on purpose: usual Vite default is 5173.
export default defineConfig({
  plugins: [react()],
  server: { port: 5180, strictPort: true },
  preview: { port: 5180, strictPort: true },
});
