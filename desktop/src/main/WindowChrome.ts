import { BrowserWindow, nativeTheme } from 'electron'

/**
 * Encapsulates the Win11 Mica/Acrylic backdrop swap and dark-mode coupling.
 *
 * `setBackgroundMaterial` works at runtime in Electron 27+ (we ship 39).
 * Acrylic = stronger frosted-glass blur — used during the splash for drama.
 * Mica = subtle wallpaper bleed-through — calmer steady state for reading.
 *
 * On non-Windows platforms the call is a no-op; we still set the dark
 * `themeSource` so native dialogs match.
 */
export type BackdropMaterial = 'acrylic' | 'mica' | 'tabbed' | 'none'

export class WindowChrome {
  static applyDarkSystemTheme(): void {
    nativeTheme.themeSource = 'dark'
  }

  static setBackdrop(window: BrowserWindow, material: BackdropMaterial): void {
    if (process.platform !== 'win32') return
    try {
      window.setBackgroundMaterial(material)
    } catch {
      // setBackgroundMaterial throws on Win10 / older builds; safe to ignore.
    }
  }
}
