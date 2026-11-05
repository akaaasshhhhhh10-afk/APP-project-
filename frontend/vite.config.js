import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Flask owns auth/alumni/mentorship; FastAPI owns events/notifications/search/stats/uploads.
const flask = 'http://127.0.0.1:5000';
const fastapi = 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api/auth': flask,
      '/api/alumni': flask,
      '/api/mentorship': flask,
      '/api/events': fastapi,
      '/api/notifications': fastapi,
      '/api/search': fastapi,
      '/api/stats': fastapi,
      '/uploads': fastapi,
    },
  },
});
