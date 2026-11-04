// Splits the writer's markdown into the sections it actually produced. Nothing is added or dropped.
export function parseReport(md) {
  const lines = md.replace(/\r/g, '').split('\n')
  let fence = false
  const heads = []
  lines.forEach((l, i) => {
    if (/^\s*```/.test(l)) fence = !fence
    const m = !fence && l.match(/^(#{1,4})\s+(.*?)\s*#*\s*$/)
    if (m) heads.push({ i, level: m[1].length, text: m[2].replace(/[*_`]/g, '') })
  })
  let title = null
  const firstContent = lines.findIndex(l => l.trim())
  if (heads[0] && heads[0].level === 1 && heads[0].i === firstContent && heads.filter(h => h.level === 1).length === 1) {
    title = heads.shift().text
    lines[firstContent] = ''
  }
  if (!heads.length) return { title, preamble: '', sections: [], raw: lines.join('\n').trim() }
  const lvl = Math.min(...heads.map(h => h.level))
  const marks = heads.filter(h => h.level === lvl)
  const slug = t => t.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  const sections = marks.map((h, k) => ({
    id: slug(h.text) || `s${k}`, title: h.text,
    body: lines.slice(h.i + 1, marks[k + 1] ? marks[k + 1].i : lines.length).join('\n').trim(),
  }))
  const preamble = lines.slice(0, marks[0].i).join('\n').trim()
  return sections.length < 2
    ? { title, preamble: '', sections: [], raw: lines.join('\n').trim() }
    : { title, preamble, sections, raw: '' }
}

// The critic prompt demands: Score / Strengths / Areas to Improve / One line verdict.
export function parseCritic(text) {
  const s = (text || '').replace(/\*\*/g, '')
  const score = s.match(/Score:\s*(\d+(?:\.\d+)?)\s*\/\s*10/i)
  const str = s.match(/Strengths:\s*([\s\S]*?)(?=Areas to Improve:)/i)
  const imp = s.match(/Areas to Improve:\s*([\s\S]*?)(?=One[- ]line verdict:)/i)
  const ver = s.match(/One[- ]line verdict:\s*([\s\S]*)$/i)
  if (!(score && str && imp && ver)) return null
  const items = b => b.split('\n').map(l => l.trim().replace(/^[-*•]\s*/, '')).filter(Boolean)
  return { score: score[1], strengths: items(str[1]), improvements: items(imp[1]), verdict: ver[1].trim() }
}
