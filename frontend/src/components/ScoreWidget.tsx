interface Props {
  score: number | null
  label: string
}

function scoreStyle(score: number) {
  if (score >= 0.7) return { text: 'text-emerald-400', ring: 'ring-emerald-500/20', bg: 'bg-emerald-900/10' }
  if (score >= 0.3) return { text: 'text-amber-400',   ring: 'ring-amber-500/20',   bg: 'bg-amber-900/10' }
  return              { text: 'text-rose-400',    ring: 'ring-rose-500/20',    bg: 'bg-rose-900/10' }
}

export default function ScoreWidget({ score, label }: Props) {
  const style = score !== null ? scoreStyle(score) : null

  return (
    <div className={[
      'flex flex-col items-center justify-center rounded-xl border border-border px-4 py-4 ring-1',
      style ? `${style.bg} ${style.ring}` : 'bg-surface2 ring-transparent',
    ].join(' ')}>
      <span className={`text-3xl font-extrabold leading-none tabular-nums ${style ? style.text : 'text-accent2'}`}>
        {score === null ? '—' : score.toFixed(3)}
      </span>
      <span className="mt-1.5 text-[10px] font-semibold uppercase tracking-widest text-gray-600">{label}</span>
    </div>
  )
}
