import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

import type { BackdropMaterial } from '../main/WindowChrome'

/**
 * Typed surface exposed to the renderer as `window.api`. Channel names
 * mirror those registered in `main/IpcRouter.ts` — every entry here has
 * a matching ipcMain.handle there or the call rejects.
 */
class WindowApi {
  close(): Promise<void> {
    return ipcRenderer.invoke('window:close')
  }
  minimize(): Promise<void> {
    return ipcRenderer.invoke('window:minimize')
  }
  maximizeToggle(): Promise<void> {
    return ipcRenderer.invoke('window:maximize-toggle')
  }
  isMaximized(): Promise<boolean> {
    return ipcRenderer.invoke('window:is-maximized')
  }
  setBackdrop(material: BackdropMaterial): Promise<void> {
    return ipcRenderer.invoke('window:set-backdrop', material)
  }
}

const api = {
  window: new WindowApi()
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error('preload contextBridge failed:', error)
  }
} else {
  // Fallback for the (rare) case context isolation is off in dev.
  // The window typings are augmented in preload/index.d.ts but TS
  // node-side config doesn't load that augmentation, so we cast.
  const w = window as unknown as { electron: typeof electronAPI; api: typeof api }
  w.electron = electronAPI
  w.api = api
}

export type Api = typeof api
