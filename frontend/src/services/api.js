export async function startResearch(topic) {
  const res = await fetch('/api/research', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(typeof body.detail === 'string' ? body.detail : 'The backend rejected this topic. Use 3–300 characters.')
  }
  return (await res.json()).job_id
}

export async function getJob(id) {
  const res = await fetch(`/api/research/${id}`)
  if (res.status === 404) throw new Error('This research job no longer exists. The server may have restarted.')
  if (!res.ok) throw new Error('Could not load the research job.')
  return res.json()
}

export const exportUrl = (id, ext) => `/api/research/${id}/report.${ext}`

/** SSE with resume. The browser re-sends Last-Event-ID on automatic reconnects; `after`
 *  covers a fresh page load. Closes itself once the job reaches a terminal state. */
export function subscribe(jobId, after, h) {
  const es = new EventSource(`/api/research/${jobId}/events?after=${after}`)
  es.onopen = () => h.onOpen?.()
  es.onmessage = m => {
    const ev = JSON.parse(m.data)
    h.onEvent(ev)
    if (ev.type === 'job' && (ev.status === 'completed' || ev.status === 'failed')) es.close()
  }
  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) h.onFatal(new Error('The live connection was closed by the server.'))
    else h.onReconnecting?.()
  }
  return () => es.close()
}
