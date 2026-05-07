import { ipcMain } from 'electron'

import { BackdropMaterial } from './WindowChrome'
import { MainWindow } from './MainWindow'

/**
 * Centralised IPC handler registration. Renderer talks to the main process
 * exclusively through these named channels (exposed as `window.api` via
 * the preload script). Adding a new IPC operation = adding it here AND in
 * preload/index.ts so the typed surface stays in lock-step.
 */
export class IpcRouter {
  private readonly mainWindow: MainWindow

  constructor(mainWindow: MainWindow) {
    this.mainWindow = mainWindow
  }

  register(): void {
    ipcMain.handle('window:close', () => this.mainWindow.instance.close())
    ipcMain.handle('window:minimize', () => this.mainWindow.instance.minimize())
    ipcMain.handle('window:maximize-toggle', () => this.toggleMaximize())
    ipcMain.handle('window:is-maximized', () => this.mainWindow.instance.isMaximized())
    ipcMain.handle('window:set-backdrop', (_evt, material: BackdropMaterial) =>
      this.mainWindow.setBackdrop(material)
    )
  }

  private toggleMaximize(): void {
    const w = this.mainWindow.instance
    if (w.isMaximized()) {
      w.unmaximize()
    } else {
      w.maximize()
    }
  }

  static disposeAll(): void {
    ipcMain.removeHandler('window:close')
    ipcMain.removeHandler('window:minimize')
    ipcMain.removeHandler('window:maximize-toggle')
    ipcMain.removeHandler('window:is-maximized')
    ipcMain.removeHandler('window:set-backdrop')
  }
}

// Re-export so this file owns the channel-name surface that preload imports.
export const IPC_CHANNELS = {
  windowClose: 'window:close',
  windowMinimize: 'window:minimize',
  windowMaximizeToggle: 'window:maximize-toggle',
  windowIsMaximized: 'window:is-maximized',
  windowSetBackdrop: 'window:set-backdrop'
} as const
