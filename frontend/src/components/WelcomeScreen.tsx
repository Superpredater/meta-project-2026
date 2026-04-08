const STEPS = [
  { num: 1, icon: '🎯', title: 'Pick a Task', desc: 'Choose Easy, Medium, or Hard from the sidebar to begin an episode.' },
  { num: 2, icon: '📖', title: 'Read the Email', desc: 'Carefully read the email subject, body, and any attachments.' },
  { num: 3, icon: '⚙️', title: 'Take Action', desc: 'Categorize, prioritize, reply, escalate, archive, or delete.' },
  { num: 4, icon: '📊', title: 'See Your Score', desc: 'Get instant per-step feedback and a final episode score.' },
]

const FEATURES = [
  { icon: '🏷️', label: 'Categorize', desc: 'spam · billing · support · general' },
  { icon: '⚡', label: 'Prioritize', desc: 'High · Medium · Low urgency' },
  { icon: '↩️', label: 'Reply', desc: 'Draft a contextual response' },
  { icon: '🚨', label: 'Escalate', desc: 'Route to a human agent' },
  { icon: '📦', label: 'Archive', desc: 'Store for later reference' },
  { icon: '🗑️', label: 'Delete', desc: 'Remove from inbox' },
]

export default function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center w-full py-12 px-8 text-center animate-fade-in">
      {/* Hero */}
      <div className="mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-surface2 border border-border mb-6 shadow-card">
          <span className="text-4xl">📬</span>
        </div>
        <h1 className="text-4xl font-extrabold text-white mb-3 tracking-tight">
          OpenEnv Email Triage
        </h1>
        <p className="text-gray-400 max-w-lg mx-auto text-base leading-relaxed">
          A reinforcement-learning benchmark environment. Process emails one at a time
          and earn rewards for correct triage decisions.
        </p>
      </div>

      {/* How it works */}
      <div className="w-full max-w-2xl mb-10">
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">How it works</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {STEPS.map((step) => (
            <div
              key={step.num}
              className="bg-surface border border-border rounded-xl p-4 flex flex-col items-center gap-2 text-center hover:border-accent/40 transition-colors"
            >
              <div className="w-7 h-7 rounded-full bg-accent/20 border border-accent/30 flex items-center justify-center text-accent2 text-xs font-bold">
                {step.num}
              </div>
              <span className="text-lg">{step.icon}</span>
              <span className="text-white text-xs font-semibold">{step.title}</span>
              <span className="text-gray-500 text-xs leading-snug">{step.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Available operations */}
      <div className="w-full max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">Available Operations</p>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {FEATURES.map((f) => (
            <div
              key={f.label}
              className="bg-surface2 border border-border rounded-lg p-3 flex flex-col items-center gap-1"
            >
              <span className="text-xl">{f.icon}</span>
              <span className="text-white text-xs font-semibold">{f.label}</span>
              <span className="text-gray-600 text-[10px] leading-tight">{f.desc}</span>
            </div>
          ))}
        </div>
      </div>

      <p className="mt-10 text-sm text-gray-600">
        ← Select a task from the sidebar to start
      </p>
    </div>
  )
}
