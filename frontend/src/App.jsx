import { useState } from 'react'
import Landing from './pages/Landing.jsx'
import Workspace from './pages/Workspace.jsx'

const hasJob = () => new URLSearchParams(window.location.search).has('job')

export default function App() {
  const [view, setView] = useState({ page: hasJob() ? 'workspace' : 'landing', topic: '', key: 0 })
  const open = (topic = '') => { window.scrollTo(0, 0); setView(v => ({ page: 'workspace', topic, key: v.key + 1 })) }
  return view.page === 'landing'
    ? <Landing onStart={open} />
    : <Workspace key={view.key} initialTopic={view.topic} onHome={() => setView(v => ({ ...v, page: 'landing' }))} />
}
