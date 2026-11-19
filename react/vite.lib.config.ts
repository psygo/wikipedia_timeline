import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    lib: { entry: 'src/index.ts', formats: ['es'], fileName: () => 'timeline-rail-react.js' },
    rollupOptions: { external: ['react', 'react-dom', 'react/jsx-runtime'], output: { assetFileNames: 'style.css' } },
    cssCodeSplit: false,
  },
});
