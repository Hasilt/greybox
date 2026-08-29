import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In docker compose this is passed as http://backend:8000
const target = process.env.VITE_API_TARGET || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/health': { target, changeOrigin: true },
    },
  },
});
