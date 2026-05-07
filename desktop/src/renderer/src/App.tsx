import { TitleBar } from './components/TitleBar'

/**
 * Empty canvas — Step 1 of the rebuild. Just the chrome (frameless
 * window with Mac-style traffic lights and an Obsidian-dark backdrop).
 * Subsequent PRs add the splash, sidebar, list, reader.
 */
export default function App(): React.JSX.Element {
  return (
    <div className="h-screen w-screen flex flex-col">
      <TitleBar />
      <main className="flex-1" />
    </div>
  )
}
