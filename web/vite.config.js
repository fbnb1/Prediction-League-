import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In dev, proxy /api/* to the gateway so the SPA and backend share an origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
    },
  },
});
