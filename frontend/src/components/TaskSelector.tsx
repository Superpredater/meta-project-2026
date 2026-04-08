import type { TaskMeta } from '../types'

interface Props {
  activeTask: string | null
  taskScores: Record<string, number>
  taskProgress: Record<string, { step: number; total: number }>
  onSelect: (taskId: string) => void
  loading: boolean
}

const TASKS: TaskMeta[] = [
  { id: 'categorize_easy', name: 'Categorize', difficulty: 'Easy',   description: 'Label 10 emails into 4 categories.', inboxSize: 10 },
  { id: 'triage_medium',   name: 'Triage',     difficulty: 'Medium', description: 'Assign priority & draft replies for 15 emails.', inboxSize: 15 },
  { id: 'manage_hard',     name: 'Full Manage',difficulty: 'Hard',   description: 'Apply all 6 operations across 25 emails.', inboxSize: 25 },
]

const DIFF_STYLES: Record<string, { badge: string; bar: string }> = {
  Easy:   { badge: 'bg-emerald-900/50 text-emerald-400 border-emerald-700/50', bar: 'bg-emerald-500' },
  Medium: { badge: 'bg-amber-900/50 text-amber-400 border-amber-700/50',       bar: 'bg-amber-500' },
  Hard:   { badge: 'bg-rose-900/50 text-rose-400 border-rose-700/50',          bar: 'bg-rose-500' },
}

const DIFF_ICONS: Record<string, string> = { Easy: '🟢', Medium: '🟡', Hard: '🔴' }

export default function TaskSelector({ activeTask, taskScores, taskProgress, onSelect, loading }: Props) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-[11px] font-semibold uppercase tracking-widest text-gray-500 px-1 mb-1">
        Tasks
      </h2>
      {TASKS.map((task) => {
        const isActive = activeTask === task.id
        const isLoading = loading && isActive
        const progress = taskProgress[task.id]
        const score = taskScores[task.id]
        const pct = progress ? Math.min(100, Math.round((progress.step / progress.total) * 100)) : 0
        const diff = DIFF_STYLES[task.difficulty]

        return (
          <button
            key={task.id}
            onClick={() => !loading && onSelect(task.id)}
            disabled={loading}
            className={[
              'relative text-left rounded-xl p-3.5 border transition-all duration-200 focus-visible:outline-none group',
              isActive
                ? 'border-accent/60 bg-surface2 shadow-glow-accent'
                : 'border-border bg-surface hover:border-accent/30 hover:bg-surface2/60',
              loading && !isActive ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
            ].join(' ')}
          >
            {/* Active indicator */}
            {isActive && (
              <div className="absolute left-0 top-3 bottom-3 w-0.5 rounded-full bg-accent" />
            )}

            {/* Loading spinner */}
            {isLoading && (
              <div className="absolute inset-0 rounded-xl flex items-center justify-center bg-surface2/80 z-10 backdrop-blur-sm">
                <svg className="animate-spin h-5 w-5 text-accent" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              </div>
            )}

            <div className="flex items-start justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-1.5">
                <span className="text-sm">{DIFF_ICONS[task.difficulty]}</span>
                <span className="font-semibold text-white text-sm">{task.name}</span>
              </div>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${diff.badge} shrink-0`}>
                {task.difficulty}
              </span>
            </div>

            <p className="text-[11px] text-gray-500 mb-2.5 leading-relaxed">{task.description}</p>

            {/* Progress */}
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] text-gray-600">
                <span>{progress ? `${progress.step} / ${progress.total}` : `0 / ${task.inboxSize}`}</span>
                <span>{pct}%</span>
              </div>
              <div className="h-1 rounded-full bg-border overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${diff.bar}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>

            {score !== undefined && (
              <p className="text-[10px] text-accent2 font-semibold mt-1.5">
                Best score: {score.toFixed(3)}
              </p>
            )}
          </button>
        )
      })}
    </div>
  )
}
