import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Define the base path for static assets to match Flask's static folder
  base: '/static/dist/',
  build: {
    // Output the build into the static folder Flask serves
    outDir: 'static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: 'index.html',
    },
  },
  server: {
    proxy: {
      // Proxying all API and Auth requests to the FastAPI backend
      '/api': 'http://localhost:5000',
      '/auth': 'http://localhost:5000',
    },
  },
});