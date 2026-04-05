import type { Reward } from '../types'

interface Props {
  reward: Reward | null
  visible: boolean
}

function scoreStyle(score: number) {
  if (score >= 0.7) return { badge: 'text-emerald-400 border-emerald-700/60 bg-emerald-900/30', bar: 'bg-emerald-500', label: 'Great' }
  if (score >= 0.3) return { badge: 'text-amber-400 border-amber-700/60 bg-amber-900/30', bar: 'bg-amber-500', label: 'Partial' }
  return { badge: 'text-rose-400 border-rose-700/60 bg-rose-900/30', bar: 'bg-rose-500', label: 'Miss' }
}

export default function RewardToast({ reward, visible }: Props) {
  if (!reward) return null

  const style = scoreStyle(reward.score)

  return (
    <div
      className={[
        'rounded-xl border border-border bg-surface overflow-hidden transition-all duration-300',
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2 pointer-events-none',
      ].join(' ')}
    >
      {/* Score bar */}
      <div className="h-0.5 w-full bg-border">
        <div
          className={`h-full transition-all duration-700 ${style.bar}`}
          style={{ width: `${Math.max(0, Math.min(100, reward.score * 100))}%` }}
        />
      </div>

      <div className="px-4 py-3 flex items-center gap-4">
        {/* Score badge */}
        <div className={`shrink-0 rounded-lg border px-3 py-2 text-center min-w-[60px] ${style.badge}`}>
          <div className="text-lg font-extrabold leading-none">{reward.score.toFixed(2)}</div>
          <div className="text-[9px] font-semibold uppercase tracking-wider mt-0.5 opacity-70">{style.label}</div>
        </div>

        {/* Rationale */}
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-0.5">Step Feedback</p>
          <p className="text-sm text-gray-300 leading-snug line-clamp-2">
            {reward.rationale}
          </p>
        </div>
      </div>
    </div>
  )
}
