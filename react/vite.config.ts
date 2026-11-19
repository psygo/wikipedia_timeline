import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The demo app (npm run dev). The library build is vite.lib.config.ts.
export default defineConfig({ plugins: [react()], root: 'demo', server: { fs: { allow: ['..', '../..'] } } });
