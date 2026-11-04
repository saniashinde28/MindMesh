import { useCallback, useEffect, useRef, useState } from 'react'
import { Check, Loader2, X, Circle, Copy, Download, FileText, Plus } from 'lucide-react'
import { AGENTS } from '../agents.js'
import { getJob, startResearch, subscribe, exportUrl } from '../services/api.js'
import { Md } from '../components/Md.jsx'
import ReportView from '../components/ReportView.jsx'
import ReviewView from '../components/ReviewView.jsx'
import { parseCritic } from '../lib/parse.js'

const blank = () => Object.fromEntries(AGENTS.map(a => [a.id, { status: 'waiting', error: null }]))
const LABEL = { waiting: 'Waiting', running: 'Running', completed: 'Completed', failed: 'Failed' }
const PILL = { idle: 'Ready', queued: 'Queued', running: 'Research in progress', completed: 'Research complete', failed: 'Research failed' }
const StatusIcon = ({ s }) => s === 'running' ? <Loader2 size={16} className="spin" /> : s === 'completed' ? <Check size={16} /> : s === 'failed' ? <X size={16} /> : <Circle size={14} />
const dur = s => s.started_at && s.finished_at ? `${Math.max(1, Math.round(s.finished_at - s.started_at))}s` : ''
const setQuery = id => window.history.replaceState(null, '', id ? `?job=${id}` : window.location.pathname)

export default function Workspace({ initialTopic, onHome }) {
  const [topic, setTopic] = useState(initialTopic)
  const [job, setJob] = useState(null)
  const [err, setErr] = useState('')
  const [live, setLive] = useState(true)
  const [tab, setTab] = useState('report')
  const [copied, setCopied] = useState(false)
  const stop = useRef(null)
  const seq = useRef(0)

  const status = job?.status ?? 'idle'
  const running = status === 'queued' || status === 'running'
  const result = status === 'completed' ? job.result : null

  // The server snapshot is the source of truth; SSE events tell us when to re-read it.
  const track = useCallback(id => {
    stop.current?.()
    const sync = async () => {
      try {
        const s = await getJob(id)
        if (s.last_seq >= seq.current) { seq.current = s.last_seq; setJob(s); setTopic(t => t || s.topic) }
      } catch (e) { setErr(e.message) }
    }
    stop.current = subscribe(id, seq.current, {
      onOpen: () => { setLive(true); sync() },
      onEvent: sync,
      onReconnecting: () => setLive(false),
      onFatal: e => { setErr(e.message); setLive(true) },
    })
  }, [])

  async function run(t = topic) {
    if (t.trim().length < 3) return
    stop.current?.(); seq.current = 0
    setErr(''); setTab('report'); setLive(true)
    setJob({ status: 'queued', topic: t.trim(), stages: blank(), result: null, error: null })
    try {
      const id = await startResearch(t.trim())
      setQuery(id); track(id)
    } catch (e) { setJob(null); setErr(e.message) }
  }

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('job')
    if (id) track(id)
    else if (initialTopic) run(initialTopic)
    return () => stop.current?.()
  }, [])

  const reset = () => { stop.current?.(); setQuery(null); seq.current = 0; setTopic(''); setJob(null); setErr('') }
  const home = () => { stop.current?.(); setQuery(null); onHome() }
  const copy = async () => { await navigator.clipboard.writeText(result.report); setCopied(true); setTimeout(() => setCopied(false), 1500) }

  const score = result ? parseCritic(result.feedback)?.score : null
  const failure = err || (status === 'failed' ? job.error : '')
  const pill = running && !live ? 'Reconnecting…' : PILL[status]

  return (
    <div className="ws">
      <header className="nav"><div className="wrap nav-in">
        <button className="logo plain" onClick={home}><span className="mark" />MindMesh</button>
        <span className={`pill ${status}`}>{pill}</span>
      </div></header>

      <main className="wrap ws-main">
        <form className="ask" onSubmit={e => { e.preventDefault(); run() }}>
          <input value={topic} onChange={e => setTopic(e.target.value)} placeholder="What do you want to research?" disabled={running} aria-label="Research topic" />
          <button className="btn primary" disabled={running || topic.trim().length < 3}>{running ? 'Researching…' : 'Start research'}</button>
        </form>

        <section className="agents" aria-live="polite">
          {AGENTS.map(a => {
            const s = job?.stages[a.id] ?? { status: 'waiting' }
            return (
              <div key={a.id} className={`agent ${s.status}`}>
                <div className="agent-top"><a.icon size={18} /><span className="st"><StatusIcon s={s.status} />{LABEL[s.status]}{dur(s) && <em>{dur(s)}</em>}</span></div>
                <h3>{a.name}</h3>
                <p>{s.status === 'running' ? a.active : s.status === 'failed' ? s.error : a.desc}</p>
              </div>
            )
          })}
        </section>

        {failure && (
          <div className="alert" role="alert"><strong>{status === 'failed' ? 'Research failed.' : 'Something went wrong.'}</strong> {failure}
            <button className="btn" onClick={status === 'failed' ? () => run() : reset}>{status === 'failed' ? 'Try again' : 'Start a new research'}</button></div>
        )}

        {result && (
          <section className="report">
            <div className="bar">
              <div className="tabs">
                {[['report', 'Report'], ['review', 'Critic review'], ['trail', 'Agent outputs']].map(([k, l]) =>
                  <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>)}
              </div>
              <div className="acts">
                <button className="btn" onClick={copy}><Copy size={15} />{copied ? 'Copied' : 'Copy'}</button>
                <a className="btn" href={exportUrl(job.id, 'md')} download><Download size={15} />Markdown</a>
                <a className="btn" href={exportUrl(job.id, 'pdf')} download><FileText size={15} />PDF</a>
                <button className="btn" onClick={reset}><Plus size={15} />New</button>
              </div>
            </div>
            {tab === 'report' && <ReportView topic={job.topic} report={result.report} score={score}
              date={new Date(job.created_at * 1000).toLocaleDateString(undefined, { dateStyle: 'long' })} />}
            {tab === 'review' && <ReviewView text={result.feedback} />}
            {tab === 'trail' && (
              <div className="trail rv-pad prose">
                <details open><summary>Search Agent output</summary><Md>{result.search_results}</Md></details>
                <details><summary>Reader Agent output</summary><Md>{result.scraped_content}</Md></details>
              </div>
            )}
          </section>
        )}
        {!job && !failure && <p className="empty">Enter a topic to start. Each agent's status appears here as it works.</p>}
      </main>
    </div>
  )
}
