export type Operation =
  | 'categorize' | 'prioritize' | 'reply'
  | 'escalate'   | 'archive'    | 'delete' | 'skip'

export interface Email {
  id: string
  subject: string
  sender: string
  body: string
  timestamp: string
  thread_id: string
  labels: string[]
  attachments: string[]
}

export interface Observation {
  email: Email
  inbox_size: number
  step_number: number
  task_id: string
}

export interface Action {
  operation: Operation
  label?: string | null
  priority?: number | null
  reply_text?: string | null
}

export interface Reward {
  score: number
  partial_scores: Record<string, number>
  rationale: string
}

export interface StepResult {
  observation: Observation | null
  reward: Reward
  done: boolean
  info: Record<string, unknown>
}

export interface HistoryEntry {
  step: number
  operation: Operation
  score: number
  rationale: string
}

export type TaskId = 'categorize_easy' | 'triage_medium' | 'manage_hard'

export interface TaskMeta {
  id: TaskId
  name: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
  description: string
  inboxSize: number
}
