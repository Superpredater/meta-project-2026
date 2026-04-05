import type { Email } from '../types'

interface Props {
  email: Email
  stepNumber: number
  inboxSize: number
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      weekday: 'short', year: 'numeric', month: 'short',
      day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  } catch { return ts }
}

function getInitials(sender: string): string {
  const name = sender.split('@')[0].replace(/[._-]/g, ' ')
  return name.split(' ').slice(0, 2).map(w => w[0]?.toUpperCase() ?? '').join('')
}

function getAvatarColor(sender: string): string {
  const colors = [
    'bg-violet-600', 'bg-blue-600', 'bg-emerald-600',
    'bg-amber-600', 'bg-rose-600', 'bg-cyan-600', 'bg-pink-600', 'bg-teal-600',
  ]
  let hash = 0
  for (const c of sender) hash = (hash * 31 + c.charCodeAt(0)) & 0xffffffff
  return colors[Math.abs(hash) % colors.length]
}

function getSenderName(sender: string): string {
  return sender.split('@')[0].replace(/[._-]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function getSenderDomain(sender: string): string {
  return sender.includes('@') ? sender.split('@')[1] : ''
}

/** Detect urgency signals from subject/body */
function getUrgencyHint(subject: string, body: string): { label: string; color: string } | null {
  const text = (subject + ' ' + body).toLowerCase()
  if (/urgent|immediate|critical|down|outage|emergency|asap|503|error/.test(text))
    return { label: 'Urgent', color: 'bg-rose-900/40 border-rose-500/50 text-rose-400' }
  if (/invoice|payment|billing|overdue|refund|charge/.test(text))
    return { label: 'Billing', color: 'bg-amber-900/40 border-amber-500/50 text-amber-400' }
  if (/spam|winner|prize|gift card|congratulations|click here|free/.test(text))
    return { label: 'Suspicious', color: 'bg-orange-900/40 border-orange-500/50 text-orange-400' }
  if (/support|help|issue|problem|broken|not working/.test(text))
    return { label: 'Support', color: 'bg-blue-900/40 border-blue-500/50 text-blue-400' }
  return null
}

/** Wrap plain body text into paragraphs for readability */
function renderBody(body: string) {
  if (!body?.trim()) return <p className="text-gray-600 italic">No message body.</p>
  return body.split(/\n{2,}/).map((para, i) => (
    <p key={i} className="mb-3 last:mb-0 whitespace-pre-wrap leading-relaxed">{para.trim()}</p>
  ))
}

export default function EmailViewer({ email, stepNumber, inboxSize }: Props) {
  const initials = getInitials(email.sender)
  const avatarColor = getAvatarColor(email.sender)
  const senderName = getSenderName(email.sender)
  const senderDomain = getSenderDomain(email.sender)
  const urgency = getUrgencyHint(email.subject, email.body)

  return (
    <div className="rounded-xl border border-border bg-surface shadow-card overflow-hidden animate-slide-up">

      {/* Top chrome bar — mimics an email client toolbar */}
      <div className="flex items-center justify-between px-5 py-2.5 bg-surface2/60 border-b border-border">
        <div className="flex items-center gap-2 text-[11px] text-gray-600">
          <span className="font-mono">📨</span>
          <span>Inbox</span>
          <span className="text-gray-700">/</span>
          <span className="text-gray-400 truncate max-w-[200px]">{email.subject}</span>
        </div>
        <div className="flex items-center gap-3">
          {urgency && (
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${urgency.color}`}>
              {urgency.label}
            </span>
          )}
          <span className="text-[11px] text-gray-600 font-mono">{stepNumber} / {inboxSize}</span>
        </div>
      </div>

      {/* Subject */}
      <div className="px-6 pt-5 pb-3">
        <h2 className="text-lg font-bold text-white leading-snug">{email.subject}</h2>
      </div>

      {/* Sender / recipient row */}
      <div className="px-6 pb-4 border-b border-border">
        <div className="flex items-start gap-3">
          <div className={`w-10 h-10 rounded-full ${avatarColor} flex items-center justify-center text-white text-sm font-bold shrink-0 mt-0.5`}>
            {initials || '?'}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <span className="text-sm font-semibold text-white">{senderName}</span>
                <span className="text-xs text-gray-500 ml-1.5">&lt;{email.sender}&gt;</span>
                <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                  <span className="text-[10px] text-gray-600">via {senderDomain}</span>
                  {email.labels.length > 0 && (
                    <>
                      <span className="text-gray-700">·</span>
                      {email.labels.map(l => (
                        <span key={l} className="text-[10px] px-1.5 py-0.5 rounded bg-surface2 border border-border text-gray-400 capitalize">
                          {l}
                        </span>
                      ))}
                    </>
                  )}
                </div>
              </div>
              <span className="text-xs text-gray-500 shrink-0 mt-0.5">{formatDate(email.timestamp)}</span>
            </div>

            {/* To / Thread metadata */}
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-0.5 text-[11px] text-gray-600">
              <span><span className="text-gray-700">To:</span> you@inbox.local</span>
              <span><span className="text-gray-700">Thread:</span> {email.thread_id}</span>
              <span><span className="text-gray-700">ID:</span> {email.id}</span>
              {email.attachments.length > 0 && (
                <span><span className="text-gray-700">📎</span> {email.attachments.length} attachment{email.attachments.length > 1 ? 's' : ''}</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="px-6 py-5 text-sm text-gray-200 max-h-72 overflow-y-auto">
        {renderBody(email.body)}
      </div>

      {/* Attachments */}
      {email.attachments.length > 0 && (
        <div className="px-6 pb-5 border-t border-border pt-4">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-600 mb-2">
            📎 Attachments ({email.attachments.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {email.attachments.map((file) => (
              <span
                key={file}
                className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-surface2 border border-border text-gray-300 hover:border-accent/40 transition-colors"
              >
                <svg className="w-3.5 h-3.5 text-gray-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                {file}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Footer hint */}
      <div className="px-6 py-2.5 border-t border-border bg-surface2/30 text-[10px] text-gray-700 flex items-center justify-between">
        <span>Choose an action below to process this email</span>
        <span className="font-mono">{email.id}</span>
      </div>
    </div>
  )
}
