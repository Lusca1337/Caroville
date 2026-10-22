import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// A porta 5173 é a única liberada no CORS da API. Se ela estiver ocupada, o Vite avisa em vez de trocar de porta.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
});
