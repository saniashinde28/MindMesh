import { Fragment } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const link = props => <a {...props} target="_blank" rel="noreferrer" />
export const Md = ({ children }) => <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: link }}>{children}</ReactMarkdown>
export const Inline = ({ children }) => <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: link, p: Fragment }}>{children}</ReactMarkdown>
