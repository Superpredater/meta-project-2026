import { useEpisode } from './hooks/useEpisode'
import TaskSelector from './components/TaskSelector'
import ScoreWidget from './components/ScoreWidget'
import HistoryPanel from './components/HistoryPanel'
import WelcomeScreen from './components/WelcomeScreen'
import StepBar from './components/StepBar'
import EmailViewer from './components/EmailViewer'
import RewardToast from './components/RewardToast'
import ActionPanel from './components/ActionPanel'
import EpisodeCompleteModal from './components/EpisodeCompleteModal'

export default function App() {
  const ep = useEpisode()

  return (
    <div className="h-screen flex flex-col bg-bg text-slate-200 overflow-hidden">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 h-14 flex items-center justify-between px-5 bg-surface border-b border-border shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-accent/20 border border-accent/30 flex items-center justify-center text-lg">
            📧
          </div>
          <span className="font-bold text-white text-sm tracking-tight">OpenEnv Email Triage</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface2 border border-border text-accent2 font-semibold">
            v1.0
          </span>
        </div>

        <div className="flex items-center gap-3">
          {(ep.activeTask || Object.keys(ep.taskScores).length > 0) && (
            <button
              onClick={ep.resetAll}
              className="text-xs px-3 py-1.5 rounded-lg border border-border text-gray-500 hover:border-rose-500/50 hover:text-rose-400 hover:bg-rose-900/10 transition-colors font-medium"
              title="Reset all results and scores"
            >
              ↺ Reset All
            </button>
          )}
          <div className="flex items-center gap-2">
          <span className={[
            'w-2 h-2 rounded-full',
            ep.online ? 'bg-emerald-400 animate-pulse-dot' : 'bg-gray-600',
          ].join(' ')} />
          <span className={`text-xs font-medium ${ep.online ? 'text-emerald-400' : 'text-gray-500'}`}>
            {ep.online ? 'API Online' : 'API Offline'}
          </span>
          </div>
        </div>
      </header>

      {/* ── Error banner ────────────────────────────────────────────── */}
      {ep.error && (
        <div className="shrink-0 bg-rose-950/80 border-b border-rose-800/60 px-5 py-2 text-xs text-rose-300 text-center font-medium animate-fade-in">
          ⚠️ {ep.error}
        </div>
      )}

      {/* ── Body ────────────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">

        {/* Sidebar */}
        <aside className="w-64 shrink-0 flex flex-col gap-4 overflow-y-auto bg-surface border-r border-border p-4">
          <TaskSelector
            activeTask={ep.activeTask}
            taskScores={ep.taskScores}
            taskProgress={ep.taskProgress}
            onSelect={ep.selectTask}
            loading={ep.loading}
          />

          <div className="border-t border-border" />

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-600 mb-2">Score</p>
            <ScoreWidget score={ep.runningScore} label="Running Score" />
          </div>

          <div className="border-t border-border" />

          <div className="flex-1 min-h-0">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-600 mb-2">Step History</p>
            <HistoryPanel history={ep.stepHistory} />
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 overflow-hidden flex flex-col min-w-0">

          {/* Welcome */}
          {ep.obs === null && ep.activeTask === null && !ep.done && (
            <div className="flex-1 overflow-y-auto">
              <WelcomeScreen />
            </div>
          )}

          {/* Active episode */}
          {ep.obs !== null && (
            <>
              {/* Step bar */}
              <div className="shrink-0 px-5 pt-4 pb-0">
                <StepBar
                  taskId={ep.obs.task_id}
                  stepNumber={ep.obs.step_number}
                  inboxSize={ep.obs.inbox_size}
                  runningScore={ep.runningScore}
                />
              </div>

              {/* Scrollable content */}
              <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-3">
                <EmailViewer
                  email={ep.obs.email}
                  stepNumber={ep.obs.step_number}
                  inboxSize={ep.obs.inbox_size}
                />
                <RewardToast visible={ep.showToast} reward={ep.lastReward} />
              </div>

              {/* Action panel */}
              <div className="shrink-0 px-5 py-4 border-t border-border bg-surface">
                <ActionPanel
                  selectedOp={ep.selectedOp}
                  onSelectOp={ep.selectOp}
                  onSubmit={ep.submitAction}
                  disabled={ep.submitting || ep.loading}
                />
              </div>
            </>
          )}
        </main>
      </div>

      {/* Episode complete modal */}
      {ep.done && ep.finalReward !== null && ep.activeTask !== null && (
        <EpisodeCompleteModal
          reward={ep.finalReward}
          taskId={ep.activeTask}
          history={ep.stepHistory}
          onRestart={ep.restart}
          onSelectNew={ep.clearTask}
        />
      )}
    </div>
  )
}
