import { useState, useCallback, useEffect } from 'react'
import { apiReset, apiStep, checkOnline } from '../api'
import type { Action, HistoryEntry, Observation, Reward } from '../types'

interface EpisodeState {
  // Connection
  online: boolean
  // Task
  activeTask: string | null
  loading: boolean
  error: string | null
  // Episode
  obs: Observation | null
  done: boolean
  finalReward: Reward | null
  // Step
  stepHistory: HistoryEntry[]
  runningScore: number | null
  selectedOp: string | null
  submitting: boolean
  lastReward: Reward | null
  showToast: boolean
  // Progress tracking per task
  taskScores: Record<string, number>
  taskProgress: Record<string, { step: number; total: number }>
}

interface EpisodeActions {
  selectTask: (taskId: string) => void
  selectOp: (op: string) => void
  submitAction: (action: Action) => void
  restart: () => void
  clearTask: () => void
  resetAll: () => void
}

export function useEpisode(): EpisodeState & EpisodeActions {
  const [online, setOnline] = useState(false)
  const [activeTask, setActiveTask] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [obs, setObs] = useState<Observation | null>(null)
  const [done, setDone] = useState(false)
  const [finalReward, setFinalReward] = useState<Reward | null>(null)
  const [stepHistory, setStepHistory] = useState<HistoryEntry[]>([])
  const [runningScore, setRunningScore] = useState<number | null>(null)
  const [selectedOp, setSelectedOp] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [lastReward, setLastReward] = useState<Reward | null>(null)
  const [showToast, setShowToast] = useState(false)
  const [taskScores, setTaskScores] = useState<Record<string, number>>({})
  const [taskProgress, setTaskProgress] = useState<Record<string, { step: number; total: number }>>({})

  // Poll online status
  useEffect(() => {
    let cancelled = false
    const poll = async () => {
      const result = await checkOnline()
      if (!cancelled) setOnline(result)
    }
    poll()
    const interval = setInterval(poll, 10_000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const setErrorWithTimeout = useCallback((msg: string) => {
    setError(msg)
    setTimeout(() => setError(null), 4000)
  }, [])

  const selectTask = useCallback(async (taskId: string) => {
    setLoading(true)
    setError(null)
    try {
      const observation = await apiReset(taskId)
      setActiveTask(taskId)
      setObs(observation)
      setStepHistory([])
      setRunningScore(null)
      setDone(false)
      setFinalReward(null)
      setSelectedOp(null)
    } catch (e) {
      setErrorWithTimeout(e instanceof Error ? e.message : 'Failed to start task')
    } finally {
      setLoading(false)
    }
  }, [setErrorWithTimeout])

  const selectOp = useCallback((op: string) => {
    setSelectedOp(op)
  }, [])

  const submitAction = useCallback(async (action: Action) => {
    if (!activeTask) return
    setSubmitting(true)
    setError(null)
    try {
      const result = await apiStep(action)
      const { observation, reward, done: isDone } = result

      setStepHistory((prev) => [
        ...prev,
        {
          step: obs?.step_number ?? 0,
          operation: action.operation,
          score: reward.score,
          rationale: reward.rationale,
        },
      ])

      setRunningScore(reward.score)
      setLastReward(reward)
      setShowToast(true)
      setTimeout(() => setShowToast(false), 3000)

      const nextObs = observation ?? obs
      if (nextObs) {
        setTaskProgress((prev) => ({
          ...prev,
          [activeTask]: { step: nextObs.step_number, total: nextObs.inbox_size },
        }))
      }

      if (isDone) {
        setDone(true)
        setFinalReward(reward)
        setTaskScores((prev) => ({
          ...prev,
          [activeTask]: Math.max(prev[activeTask] ?? 0, reward.score),
        }))
        setObs(null)
      } else {
        setObs(observation)
      }
    } catch (e) {
      setErrorWithTimeout(e instanceof Error ? e.message : 'Failed to submit action')
    } finally {
      setSubmitting(false)
    }
  }, [activeTask, obs, setErrorWithTimeout])

  const restart = useCallback(async () => {
    if (!activeTask) return
    await selectTask(activeTask)
  }, [activeTask, selectTask])

  const clearTask = useCallback(() => {
    setActiveTask(null)
    setObs(null)
    setDone(false)
    setFinalReward(null)
    setStepHistory([])
    setRunningScore(null)
    setSelectedOp(null)
    setLastReward(null)
    setShowToast(false)
  }, [])

  const resetAll = useCallback(() => {
    setActiveTask(null)
    setObs(null)
    setDone(false)
    setFinalReward(null)
    setStepHistory([])
    setRunningScore(null)
    setSelectedOp(null)
    setLastReward(null)
    setShowToast(false)
    setTaskScores({})
    setTaskProgress({})
    setError(null)
  }, [])

  return {
    online,
    activeTask,
    loading,
    error,
    obs,
    done,
    finalReward,
    stepHistory,
    runningScore,
    selectedOp,
    submitting,
    lastReward,
    showToast,
    taskScores,
    taskProgress,
    selectTask,
    selectOp,
    submitAction,
    restart,
    clearTask,
    resetAll,
  }
}
