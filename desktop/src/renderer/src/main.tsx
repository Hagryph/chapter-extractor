import './styles/reset.css'
import './styles/tokens.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'

const rootEl = document.getElementById('root')
if (rootEl === null) {
  throw new Error('#root element not found in renderer index.html')
}

createRoot(rootEl).render(
  <StrictMode>
    <App />
  </StrictMode>
)
