export type Department = 'Engineering' | 'S&T' | 'TRD'
export type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type TrainPriority = 'HIGH' | 'NORMAL'
export type PageKey = 'maintenance' | 'planner'

export interface Train {
  number: string
  type: string
  section: string
  entry: string
  exit: string
  priority: TrainPriority
  status: string
}

export interface MaintenanceJob {
  id: string
  asset: string
  department: Department
  section: string
  work: string
  duration: number
  required_crew: string
  required_equipment: string
  preferred_start: number
  preferred_end: number
  dci: number
}

export interface TimeWindow {
  start: number
  end: number
}

export interface Conditions {
  block_window: TimeWindow
  crew_windows: Record<Department, TimeWindow>
  high_priority_trains: string[]
  train_delays: Record<string, number>
}

export interface Objectives {
  maximize_completed: boolean
  minimize_disruption: boolean
  minimize_blocks: boolean
  prioritize_critical: boolean
}

export interface IncludedTask {
  id: string
  asset: string
  work: string
  department: Department
  dci: number
}

export interface PostponedTask {
  id: string
  asset: string
  work: string
  department: Department
  reason: string
}

export interface ManualBlock {
  job_id: string
  asset: string
  work: string
  start: number
  end: number
}

export interface ManualBaseline {
  blocks: ManualBlock[]
  total_block_time: number
  disruption: number
  affected_trains: string[]
  score?: number
}

export interface OptimizeResult {
  feasible: boolean
  section?: string
  start?: number
  end?: number
  start_label?: string
  end_label?: string
  duration?: number
  included_tasks?: IncludedTask[]
  postponed_tasks?: PostponedTask[]
  train_conflicts?: number
  trains_affected?: string[]
  estimated_delay?: number
  optimization_score?: number
  explanation?: string[]
  manual_baseline?: ManualBaseline
  alternative_score?: number | null
  dci?: Record<string, number>
}
