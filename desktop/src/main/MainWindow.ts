import { BrowserWindow, shell } from 'electron'
import { join } from 'path'
import { is } from '@electron-toolkit/utils'
import { BackdropMaterial, WindowChrome } from './WindowChrome'

/**
 * Wraps a single BrowserWindow with our chrome configuration:
 *   - frameless (we render Mac-style traffic lights in React)
 *   - hiddenInset titlebar style on macOS (native traffic lights for free)
 *   - Win11 acrylic on first show, switchable to mica via setBackdrop
 *   - Obsidian dark backgroundColor while content boots
 *   - rounded outer corners (Electron handles via DwmSetWindowAttribute)
 *
 * The window is created hidden and only shown on `ready-to-show` so users
 * don't see a white flash before React renders.
 */
export class MainWindow {
  private static readonly DEFAULT_WIDTH = 1380
  private static readonly DEFAULT_HEIGHT = 860
  private static readonly MIN_WIDTH = 1200
  private static readonly MIN_HEIGHT = 720

  private readonly window: BrowserWindow

  constructor() {
    this.window = new BrowserWindow({
      width: MainWindow.DEFAULT_WIDTH,
      height: MainWindow.DEFAULT_HEIGHT,
      minWidth: MainWindow.MIN_WIDTH,
      minHeight: MainWindow.MIN_HEIGHT,
      show: false,
      frame: false,
      titleBarStyle: 'hiddenInset',
      backgroundColor: '#0e0e0f',
      backgroundMaterial: 'acrylic',
      roundedCorners: true,
      webPreferences: {
        preload: join(__dirname, '../preload/index.js'),
        sandbox: false
      }
    })

    this.attachHandlers()
    void this.loadContent()
  }

  get instance(): BrowserWindow {
    return this.window
  }

  show(): void {
    this.window.show()
  }

  setBackdrop(material: BackdropMaterial): void {
    WindowChrome.setBackdrop(this.window, material)
  }

  // ── private ──────────────────────────────────────────────────────────

  private attachHandlers(): void {
    this.window.once('ready-to-show', () => this.show())
    this.window.webContents.setWindowOpenHandler(({ url }) => {
      void shell.openExternal(url)
      return { action: 'deny' }
    })
  }

  private async loadContent(): Promise<void> {
    if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
      await this.window.loadURL(process.env['ELECTRON_RENDERER_URL'])
    } else {
      await this.window.loadFile(join(__dirname, '../renderer/index.html'))
    }
  }
}
