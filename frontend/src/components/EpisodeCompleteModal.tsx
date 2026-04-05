import type { Reward, HistoryEntry } from '../types'

interface Props {
  reward: Reward
  taskId: string
  history: HistoryEntry[]
  onRestart: () => void
  onSelectNew: () => void
}

const EMOJI: Record<string, string> = {
  categorize: '🏷️', prioritize: '⚡', reply: '↩️',
  escalate: '🚨', archive: '📦', delete: '🗑️', skip: '⏭️',
}

function scoreStyle(s: number) {
  if (s >= 0.7) return { text: 'text-emerald-400', ring: 'ring-emerald-500/20', bar: 'bg-emerald-500', border: 'border-emerald-500/40' }
  if (s >= 0.3) return { text: 'text-amber-400',   ring: 'ring-amber-500/20',   bar: 'bg-amber-500',   border: 'border-amber-500/40' }
  return              { text: 'text-rose-400',    ring: 'ring-rose-500/20',    bar: 'bg-rose-500',    border: 'border-rose-500/40' }
}

function formatDim(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function isSuccess(score: number) { return score >= 0.7 }

export default function EpisodeCompleteModal({ reward, history, onRestart, onSelectNew }: Props) {
  const { score, partial_scores, rationale } = reward
  const style = scoreStyle(score)
  const pct = Math.round(score * 100)
  const success = isSuccess(score)

  const passed = history.filter(h => isSuccess(h.score)).length
  const failed = history.length - passed

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md bg-black/70 animate-fade-in">
      <div className="bg-surface border border-border rounded-2xl shadow-card w-full max-w-lg flex flex-col overflow-hidden animate-slide-up">

        {/* Score bar at top */}
        <div className="h-1 w-full bg-border">
          <div className={`h-full transition-all duration-1000 ${style.bar}`} style={{ width: `${pct}%` }} />
        </div>

        <div className="p-7 flex flex-col gap-5 max-h-[85vh] overflow-y-auto">

          {/* Result badge + title */}
          <div className="flex flex-col items-center gap-2 text-center">
            <span className={`text-xs font-bold px-3 py-1 rounded-full border ${success ? 'bg-emerald-900/30 border-emerald-500/40 text-emerald-400' : 'bg-rose-900/30 border-rose-500/40 text-rose-400'}`}>
              {success ? '✓ SUCCESS' : '✗ FAILED'}
            </span>
            <h2 className="text-xl font-bold text-white">Episode Complete</h2>
            <p className="text-sm text-gray-500">
              {success ? 'Great work — well handled.' : 'Review your decisions below and try again.'}
            </p>
          </div>

          {/* Score ring + pass/fail summary */}
          <div className="flex items-center justify-center gap-8">
            <div className={`flex flex-col items-center justify-center w-24 h-24 rounded-full border-2 ring-4 ${style.ring} border-border bg-surface2`}>
              <span className={`text-3xl font-extrabold tabular-nums ${style.text}`}>{score.toFixed(2)}</span>
              <span className="text-[10px] text-gray-600 uppercase tracking-widest mt-0.5">score</span>
            </div>
            {history.length > 0 && (
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-sm text-gray-300">{passed} actions passed</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  <span className="text-sm text-gray-300">{failed} actions failed</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-gray-600" />
                  <span className="text-sm text-gray-500">{history.length} total steps</span>
                </div>
              </div>
            )}
          </div>

          {/* Partial score breakdown */}
          {Object.keys(partial_scores).length > 0 && (
            <div className="w-full">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-600 mb-2">Score Breakdown</p>
              <div className="flex flex-col gap-1.5">
                {Object.entries(partial_scores).map(([dim, val]) => {
                  const ds = scoreStyle(val)
                  const dpct = Math.max(0, Math.min(100, val * 100))
                  const ok = isSuccess(val)
                  return (
                    <div key={dim} className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold w-4 ${ok ? 'text-emerald-500' : 'text-rose-500'}`}>{ok ? '✓' : '✗'}</span>
                      <span className="text-[11px] text-gray-400 w-24 shrink-0">{formatDim(dim)}</span>
                      <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
                        <div className={`h-full rounded-full ${ds.bar}`} style={{ width: `${dpct}%` }} />
                      </div>
                      <span className={`text-[11px] font-bold w-8 text-right ${ds.text}`}>{val.toFixed(2)}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Action history */}
          {history.length > 0 && (
            <div className="w-full">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-600 mb-2">Action History</p>
              <div className="flex flex-col gap-1 max-h-48 overflow-y-auto pr-0.5">
                {history.map((entry) => {
                  const ok = isSuccess(entry.score)
                  const es = scoreStyle(entry.score)
                  return (
                    <div key={entry.step} className={`flex items-start gap-2.5 rounded-lg px-3 py-2 border ${ok ? 'border-emerald-500/20 bg-emerald-900/10' : 'border-rose-500/20 bg-rose-900/10'}`}>
                      <span className="text-sm shrink-0 mt-0.5">{EMOJI[entry.operation] ?? '•'}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-gray-200 capitalize">{entry.operation}</span>
                          <span className="text-[10px] text-gray-600">#{entry.step + 1}</span>
                          <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded ${ok ? 'bg-emerald-900/40 text-emerald-400' : 'bg-rose-900/40 text-rose-400'}`}>
                            {ok ? 'PASS' : 'FAIL'} {entry.score.toFixed(2)}
                          </span>
                        </div>
                        {entry.rationale && (
                          <p className="text-[10px] text-gray-500 mt-0.5 leading-relaxed line-clamp-2">{entry.rationale}</p>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Rationale */}
          {rationale && (
            <p className="text-xs text-gray-600 text-center leading-relaxed max-w-sm mx-auto">{rationale}</p>
          )}

          {/* Actions */}
          <div className="flex gap-3 w-full">
            <button
              onClick={onRestart}
              className="flex-1 bg-accent hover:bg-accent-hover text-white font-semibold rounded-lg py-2.5 text-sm transition-colors active:scale-[0.98]"
            >
              Play Again
            </button>
            <button
              onClick={onSelectNew}
              className="flex-1 border border-border hover:border-accent/40 text-gray-400 hover:text-accent2 font-semibold rounded-lg py-2.5 text-sm transition-colors"
            >
              Try Another Task
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
