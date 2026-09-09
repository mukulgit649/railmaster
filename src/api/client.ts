import {
  Conditions,
  MaintenanceJob,
  Objectives,
  OptimizeResult,
  Train,
} from '../types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status}`)
  }
  return res.json()
}

export function getSection() {
  return request<{ section: string; subsections: string[] }>('/api/section')
}

export function getConditions() {
  return request<Conditions>('/api/conditions')
}

export function getTrains() {
  return request<Train[]>('/api/trains')
}

export function getMaintenance() {
  return request<MaintenanceJob[]>('/api/maintenance')
}

export function runPrioritize() {
  return request<MaintenanceJob[]>('/api/prioritize', { method: 'POST' })
}

interface OptimizePayload {
  objectives: Objectives
  conditions?: Conditions
}

export function runOptimize(payload: OptimizePayload) {
  return request<OptimizeResult>('/api/optimize', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function runReoptimize(payload: OptimizePayload) {
  return request<OptimizeResult>('/api/reoptimize', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
