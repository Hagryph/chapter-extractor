import { app, BrowserWindow } from 'electron'
import { electronApp, optimizer } from '@electron-toolkit/utils'

import { IpcRouter } from './IpcRouter'
import { MainWindow } from './MainWindow'
import { WindowChrome } from './WindowChrome'

/**
 * Owns the Electron app lifecycle:
 *   - single-instance lock (prevents two copies fighting over the registry DB later)
 *   - app.whenReady ⇒ instantiates MainWindow + IpcRouter
 *   - macOS dock activate ⇒ recreate window if none open
 *   - non-mac ⇒ quit on last window close
 */
export class AppLifecycle {
  private static readonly APP_USER_MODEL_ID = 'com.hagryph.chapterextractor'

  private mainWindow: MainWindow | null = null
  private ipcRouter: IpcRouter | null = null

  start(): void {
    if (!app.requestSingleInstanceLock()) {
      app.quit()
      return
    }
    app.on('second-instance', this.onSecondInstance)

    app
      .whenReady()
      .then(this.onReady)
      .catch((err) => {
        console.error('AppLifecycle.onReady failed:', err)
        app.quit()
      })
    app.on('window-all-closed', this.onAllClosed)
    app.on('activate', this.onActivate)
    app.on('browser-window-created', (_event, window) => {
      // Adds F12 / Ctrl+R sane defaults in dev; no-op in prod.
      optimizer.watchWindowShortcuts(window)
    })
  }

  // ── handlers (arrow functions to preserve `this`) ──────────────────────

  private onReady = (): void => {
    electronApp.setAppUserModelId(AppLifecycle.APP_USER_MODEL_ID)
    WindowChrome.applyDarkSystemTheme()

    this.mainWindow = new MainWindow()
    this.ipcRouter = new IpcRouter(this.mainWindow)
    this.ipcRouter.register()
  }

  private onSecondInstance = (): void => {
    if (this.mainWindow === null) return
    const w = this.mainWindow.instance
    if (w.isMinimized()) w.restore()
    w.focus()
  }

  private onAllClosed = (): void => {
    if (process.platform !== 'darwin') {
      IpcRouter.disposeAll()
      app.quit()
    }
  }

  private onActivate = (): void => {
    if (BrowserWindow.getAllWindows().length === 0) {
      this.onReady()
    }
  }
}
