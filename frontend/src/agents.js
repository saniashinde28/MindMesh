import { Search, BookOpen, PenLine, ShieldCheck } from 'lucide-react'
// ids match the stage names emitted by backend/pipeline.py
export const AGENTS = [
  { id: 'search', name: 'Search Agent', icon: Search, desc: 'Finds recent, reliable sources on your topic.', active: 'Searching for relevant sources…' },
  { id: 'reader', name: 'Reader Agent', icon: BookOpen, desc: 'Picks the best result and scrapes it for depth.', active: 'Scraping the top resource…' },
  { id: 'writer', name: 'Writer', icon: PenLine, desc: 'Turns the findings into a structured report.', active: 'Drafting the research report…' },
  { id: 'critic', name: 'Critic', icon: ShieldCheck, desc: 'Reviews the report and gives feedback.', active: 'Evaluating the report…' },
]
