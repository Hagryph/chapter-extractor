import { resolve } from 'path'
import { defineConfig } from 'electron-vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  main: {},
  preload: {},
  renderer: {
    resolve: {
      alias: {
        '@renderer': resolve('src/renderer/src')
      }
    },
    // .glb is a binary asset Vite doesn't recognise by default.
    // We serve it from public/ at /models/petal.glb so this also
    // covers any future imports.
    assetsInclude: ['**/*.glb'],
    plugins: [react(), tailwindcss()]
  }
})
