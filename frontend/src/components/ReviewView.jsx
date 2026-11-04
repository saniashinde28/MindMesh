import { Md, Inline } from './Md.jsx'
import { parseCritic } from '../lib/parse.js'

export default function ReviewView({ text }) {
  const r = parseCritic(text)
  if (!r) return <div className="prose rv-pad"><Md>{text}</Md></div>  // unexpected format: show it untouched
  return (
    <div className="rev rv-pad">
      <div className="rev-top">
        <div className="rev-score"><strong>{r.score}</strong><span>/ 10</span></div>
        <p className="verdict"><Inline>{r.verdict}</Inline></p>
      </div>
      <div className="rev-cols">
        <div><h3>Strengths</h3><ul>{r.strengths.map((t, i) => <li key={i}><Inline>{t}</Inline></li>)}</ul></div>
        <div><h3>Areas to improve</h3><ul>{r.improvements.map((t, i) => <li key={i}><Inline>{t}</Inline></li>)}</ul></div>
      </div>
    </div>
  )
}
