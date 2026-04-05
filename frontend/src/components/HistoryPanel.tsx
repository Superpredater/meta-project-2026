import { useState } from 'react'
import type { HistoryEntry, Operation } from '../types'

const EMOJI: Record<Operation, string> = {
  categorize: '🏷️', prioritize: '⚡', reply: '↩️',
  escalate: '🚨', archive: '📦', delete: '🗑️', skip: '⏭️',
}

function isSuccess(score: number) { return score >= 0.7 }

interface Props { history: HistoryEntry[] }

export default function HistoryPanel({ history }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null)

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-center">
        <span className="text-2xl mb-2">📭</span>
        <p className="text-xs text-gray-600">No steps yet</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1 max-h-56 overflow-y-auto pr-0.5">
      {[...history].reverse().map((entry) => {
        const ok = isSuccess(entry.score)
        const isOpen = expanded === entry.step
        return (
          <div
            key={entry.step}
            className={`rounded-lg border overflow-hidden cursor-pointer transition-colors ${ok ? 'border-emerald-500/25 bg-emerald-900/10 hover:bg-emerald-900/20' : 'border-rose-500/25 bg-rose-900/10 hover:bg-rose-900/20'}`}
            onClick={() => setExpanded(isOpen ? null : entry.step)}
          >
            <div className="flex items-center gap-2 px-2.5 py-2">
              <span className="text-sm leading-none shrink-0">{EMOJI[entry.operation]}</span>
              <div className="flex-1 min-w-0">
                <span className="text-xs text-gray-300 capitalize font-medium">{entry.operation}</span>
                <span className="text-[10px] text-gray-600 ml-1.5">#{entry.step + 1}</span>
              </div>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 ${ok ? 'bg-emerald-900/40 text-emerald-400' : 'bg-rose-900/40 text-rose-400'}`}>
                {ok ? 'PASS' : 'FAIL'}
              </span>
              <span className={`text-xs font-bold shrink-0 w-8 text-right ${ok ? 'text-emerald-400' : 'text-rose-400'}`}>
                {entry.score.toFixed(2)}
              </span>
            </div>
            {isOpen && entry.rationale && (
              <div className="px-2.5 pb-2 text-[10px] text-gray-500 leading-relaxed border-t border-white/5 pt-1.5">
                {entry.rationale}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
