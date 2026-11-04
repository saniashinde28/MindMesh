import { useMemo } from 'react'
import { Md } from './Md.jsx'
import { parseReport } from '../lib/parse.js'

export default function ReportView({ topic, report, score, date }) {
  const p = useMemo(() => parseReport(report), [report])
  return (
    <div className="rv">
      <header className="rv-head">
        <h1>{p.title || topic}</h1>
        <p className="meta">Generated {date}{score != null && <span className="score">Critic score {score}/10</span>}</p>
      </header>
      <div className="rv-grid">
        {p.sections.length > 0 && (
          <nav className="toc" aria-label="Report sections">
            {p.sections.map(s => <a key={s.id} href={`#${s.id}`}>{s.title}</a>)}
          </nav>
        )}
        <div className="rv-main prose">
          {p.preamble && <Md>{p.preamble}</Md>}
          {p.sections.map(s => (
            <section key={s.id} id={s.id}><h2>{s.title}</h2><Md>{s.body}</Md></section>
          ))}
          {!p.sections.length && <Md>{p.raw}</Md>}
        </div>
      </div>
    </div>
  )
}
