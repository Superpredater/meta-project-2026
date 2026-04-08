interface Props {
  taskId: string
  stepNumber: number
  inboxSize: number
  runningScore: number | null
}

function formatTaskName(id: string): string {
  return id.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function scoreStyle(score: number): string {
  if (score >= 0.7) return 'text-emerald-400'
  if (score >= 0.3) return 'text-amber-400'
  return 'text-rose-400'
}

function barColor(score: number | null): string {
  if (score === null) return 'bg-accent'
  if (score >= 0.7) return 'bg-emerald-500'
  if (score >= 0.3) return 'bg-amber-500'
  return 'bg-rose-500'
}

export default function StepBar({ taskId, stepNumber, inboxSize, runningScore }: Props) {
  const pct = inboxSize > 0 ? Math.min(100, Math.round((stepNumber / inboxSize) * 100)) : 0

  return (
    <div className="bg-surface border border-border rounded-xl px-5 py-3 flex flex-col gap-2.5">
      <div className="flex items-center justify-between gap-3">
        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-surface2 border border-border text-accent2 whitespace-nowrap">
          {formatTaskName(taskId)}
        </span>

        <div className="flex items-center gap-1.5 text-sm text-gray-400">
          <span>Email</span>
          <span className="text-white font-bold">{stepNumber + 1}</span>
          <span className="text-gray-600">/</span>
          <span className="text-white font-bold">{inboxSize}</span>
        </div>

        {runningScore !== null ? (
          <span className={`text-sm font-bold whitespace-nowrap ${scoreStyle(runningScore)}`}>
            {runningScore.toFixed(3)}
          </span>
        ) : (
          <span className="text-sm text-gray-600">—</span>
        )}
      </div>

      <div className="h-1.5 rounded-full bg-border overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${barColor(runningScore)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
