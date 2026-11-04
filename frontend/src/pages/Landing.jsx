import { useState } from 'react'
import { ArrowRight, Network, Globe, Layers, ShieldCheck, FileText } from 'lucide-react'
import { AGENTS } from '../agents.js'

const FEATURES = [
  { icon: Network, t: 'Multi-agent collaboration', d: 'Four specialised agents hand work to each other, each with one job.' },
  { icon: Globe, t: 'Automated web research', d: 'A search agent finds sources and a reader agent scrapes the best one.' },
  { icon: Layers, t: 'Content synthesis', d: 'Search results and scraped pages are combined into a single report.' },
  { icon: ShieldCheck, t: 'Built-in critique', d: 'A critic agent reviews every report before you read it.' },
  { icon: FileText, t: 'Structured reports', d: 'Read the report in the app, or download it as Markdown or PDF.' },
]

export default function Landing({ onStart }) {
  const [topic, setTopic] = useState('')
  const submit = e => { e.preventDefault(); onStart(topic) }
  return (
    <>
      <header className="nav"><div className="wrap nav-in">
        <a className="logo" href="#top"><span className="mark" />MindMesh</a>
        <nav className="links"><a href="#features">Features</a><a href="#how">How it works</a><a href="#about">About</a></nav>
        <button className="btn primary" onClick={() => onStart('')}>Start researching</button>
      </div></header>

      <main id="top">
        <section className="wrap hero">
          <h1>Research smarter.<br />Think deeper.</h1>
          <p className="lead">MindMesh uses multiple specialised AI agents to search, read, write and critique, so you get a reviewed research report instead of a list of links.</p>
          <form className="ask" onSubmit={submit}>
            <input value={topic} onChange={e => setTopic(e.target.value)} placeholder="What do you want to research?" aria-label="Research topic" />
            <button className="btn primary" disabled={topic.trim().length < 3}>Start research <ArrowRight size={16} /></button>
          </form>
          <div className="mesh" aria-hidden="true">
            {AGENTS.map(a => <div className="node" key={a.id}><a.icon size={18} /><span>{a.name}</span></div>)}
          </div>
        </section>

        <section id="how" className="wrap sec">
          <h2>How it works</h2>
          <ol className="steps">
            {AGENTS.map((a, i) => (
              <li key={a.id}><span className="num">{i + 1}</span><div><h3>{a.name}</h3><p>{a.desc}</p></div></li>
            ))}
          </ol>
        </section>

        <section id="features" className="wrap sec">
          <h2>Features</h2>
          <div className="feat">
            {FEATURES.map(f => <div key={f.t}><f.icon size={20} /><h3>{f.t}</h3><p>{f.d}</p></div>)}
          </div>
        </section>

        <section id="about" className="wrap sec about">
          <h2>About</h2>
          <p>MindMesh is a Python multi-agent research system. This interface runs the real pipeline and streams each agent's status as it happens.</p>
        </section>
      </main>

      <footer><div className="wrap foot">
        <div><a className="logo" href="#top"><span className="mark" />MindMesh</a><p>Multi-agent research, reviewed before you read it.</p></div>
        <nav className="links"><a href="#features">Features</a><a href="#how">How it works</a><a href="#about">About</a></nav>
      </div></footer>
    </>
  )
}
