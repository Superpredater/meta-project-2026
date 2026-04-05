import { useState, useEffect } from 'react'
import type { Action, Operation } from '../types'

interface Props {
  selectedOp: string | null
  onSelectOp: (op: string) => void
  onSubmit: (action: Action) => void
  disabled: boolean
}

const OPS: { id: Operation; label: string; emoji: string; hint: string }[] = [
  { id: 'categorize', label: 'Categorize', emoji: '🏷️', hint: 'Assign a topic label' },
  { id: 'prioritize', label: 'Prioritize', emoji: '⚡',  hint: 'Set urgency level' },
  { id: 'reply',      label: 'Reply',      emoji: '↩️',  hint: 'Draft a response' },
  { id: 'escalate',   label: 'Escalate',   emoji: '🚨',  hint: 'Route to human agent' },
  { id: 'archive',    label: 'Archive',    emoji: '📦',  hint: 'Store for later' },
  { id: 'delete',     label: 'Delete',     emoji: '🗑️',  hint: 'Remove from inbox' },
  { id: 'skip',       label: 'Skip',       emoji: '⏭️',  hint: 'Process later' },
]

const LABELS = [
  { value: 'spam',    label: 'Spam',    icon: '🚫' },
  { value: 'billing', label: 'Billing', icon: '💳' },
  { value: 'support', label: 'Support', icon: '🛠️' },
  { value: 'general', label: 'General', icon: '📋' },
]

const PRIORITIES = [
  { value: 1, label: 'High',   icon: '🔴', desc: 'Urgent — act immediately' },
  { value: 2, label: 'Medium', icon: '🟡', desc: 'Important — handle soon' },
  { value: 3, label: 'Low',    icon: '🟢', desc: 'Routine — no rush' },
]

export default function ActionPanel({ selectedOp, onSelectOp, onSubmit, disabled }: Props) {
  const [label, setLabel] = useState('spam')
  const [priority, setPriority] = useState(1)
  const [replyText, setReplyText] = useState('')

  // Reset sub-fields when op changes
  useEffect(() => { setReplyText('') }, [selectedOp])

  function handleSubmit() {
    if (!selectedOp || disabled) return
    const action: Action = { operation: selectedOp as Operation }
    if (selectedOp === 'categorize') action.label = label
    if (selectedOp === 'prioritize') action.priority = priority
    if (selectedOp === 'reply') action.reply_text = replyText
    onSubmit(action)
  }

  const canSubmit = !!selectedOp && !disabled &&
    (selectedOp !== 'reply' || replyText.trim().length > 0)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-500">
          Choose an Action
        </h3>
        {selectedOp && (
          <span className="text-[11px] text-accent2 font-medium">
            {OPS.find(o => o.id === selectedOp)?.hint}
          </span>
        )}
      </div>

      {/* Operation buttons */}
      <div className="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
        {OPS.map((op) => {
          const isSelected = selectedOp === op.id
          return (
            <button
              key={op.id}
              onClick={() => !disabled && onSelectOp(op.id)}
              disabled={disabled}
              title={op.hint}
              className={[
                'flex flex-col items-center justify-center gap-1.5 rounded-lg px-1 py-3 text-[11px] font-semibold border transition-all duration-150 focus-visible:outline-none',
                isSelected
                  ? 'border-accent bg-accent/15 text-accent2 shadow-glow-accent'
                  : 'border-border bg-surface2 text-gray-500 hover:border-accent/40 hover:text-gray-300 hover:bg-surface3',
                disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
              ].join(' ')}
            >
              <span className="text-base leading-none">{op.emoji}</span>
              <span className="leading-none">{op.label}</span>
            </button>
          )
        })}
      </div>

      {/* Contextual sub-fields */}
      {selectedOp === 'categorize' && (
        <div className="animate-slide-up">
          <label className="block text-[11px] text-gray-500 font-medium mb-1.5">Select Label</label>
          <div className="grid grid-cols-4 gap-1.5">
            {LABELS.map((l) => (
              <button
                key={l.value}
                onClick={() => setLabel(l.value)}
                disabled={disabled}
                className={[
                  'flex flex-col items-center gap-1 py-2.5 rounded-lg border text-xs font-medium transition-all',
                  label === l.value
                    ? 'border-accent/60 bg-accent/10 text-accent2'
                    : 'border-border bg-surface2 text-gray-400 hover:border-accent/30',
                  disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
                ].join(' ')}
              >
                <span>{l.icon}</span>
                <span>{l.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedOp === 'prioritize' && (
        <div className="animate-slide-up">
          <label className="block text-[11px] text-gray-500 font-medium mb-1.5">Select Priority</label>
          <div className="flex flex-col gap-1.5">
            {PRIORITIES.map((p) => (
              <button
                key={p.value}
                onClick={() => setPriority(p.value)}
                disabled={disabled}
                className={[
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg border text-sm transition-all text-left',
                  priority === p.value
                    ? 'border-accent/60 bg-accent/10 text-white'
                    : 'border-border bg-surface2 text-gray-400 hover:border-accent/30',
                  disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
                ].join(' ')}
              >
                <span className="text-base">{p.icon}</span>
                <div>
                  <div className="font-semibold text-xs">{p.value} — {p.label}</div>
                  <div className="text-[10px] text-gray-500">{p.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedOp === 'reply' && (
        <div className="animate-slide-up">
          <label className="block text-[11px] text-gray-500 font-medium mb-1.5">
            Reply Text
            <span className="ml-1 text-gray-600">({replyText.trim().length} chars)</span>
          </label>
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            disabled={disabled}
            rows={3}
            placeholder="Type your reply to the sender…"
            className="w-full rounded-lg border border-border bg-surface2 text-gray-200 text-sm px-3 py-2.5 resize-y focus:outline-none focus:border-accent/60 disabled:opacity-40 placeholder-gray-600 leading-relaxed"
          />
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={[
          'w-full rounded-lg py-2.5 text-sm font-semibold transition-all duration-150 focus-visible:outline-none flex items-center justify-center gap-2',
          canSubmit
            ? 'bg-accent hover:bg-accent-hover text-white shadow-glow-accent cursor-pointer active:scale-[0.98]'
            : 'bg-surface2 border border-border text-gray-600 cursor-not-allowed',
        ].join(' ')}
      >
        {disabled ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Processing…
          </>
        ) : (
          'Submit Action →'
        )}
      </button>
    </div>
  )
}
