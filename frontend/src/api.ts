import type { Action, Observation, StepResult } from './types'

const BASE = ''

export async function apiReset(taskId: string): Promise<Observation> {
  const r = await fetch(`${BASE}/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_id: taskId }),
  })
  if (!r.ok) {
    const e = await r.json().catch(() => ({}))
    const detail = (e as { detail?: unknown }).detail
    throw new Error(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : `HTTP ${r.status}`)
  }
  return r.json()
}

export async function apiStep(action: Action): Promise<StepResult> {
  const r = await fetch(`${BASE}/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(action),
  })
  if (!r.ok) {
    const e = await r.json().catch(() => ({}))
    const detail = (e as { detail?: unknown }).detail
    throw new Error(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : `HTTP ${r.status}`)
  }
  return r.json()
}

export async function apiState(): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/state`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}

export async function checkOnline(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/state`)
    return r.ok
  } catch { return false }
}
