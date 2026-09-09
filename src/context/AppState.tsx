import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import * as api from '../api/client'
import {
  Conditions,
  Department,
  MaintenanceJob,
  Objectives,
  OptimizeResult,
  PageKey,
  Train,
} from '../types'

interface AppStateShape {
  page: PageKey
  setPage: (p: PageKey) => void

  section: string
  subsections: string[]

  trains: Train[]
  maintenanceJobs: MaintenanceJob[]
  loadingInitial: boolean
  loadError: string | null

  prioritizing: boolean
  prioritized: boolean
  runPrioritization: () => Promise<void>

  conditions: Conditions | null
  objectives: Objectives
  setObjective: (key: keyof Objectives, value: boolean) => void
  updateBlockWindow: (field: 'start' | 'end', minutes: number) => void
  updateCrewWindow: (dept: Department, field: 'start' | 'end', minutes: number) => void
  toggleCrewAvailable: (dept: Department, available: boolean) => void
  setTrainDelay: (trainNumber: string, minutes: number) => void
  setHighPriorityTrains: (trainNumbers: string[]) => void

  optimizing: boolean
  optimizeResult: OptimizeResult | null
  hasGenerated: boolean
  generatePlan: () => Promise<void>
  reoptimize: () => Promise<void>
}

const AppStateContext = createContext<AppStateShape | null>(null)

const DEFAULT_OBJECTIVES: Objectives = {
  maximize_completed: true,
  minimize_disruption: true,
  minimize_blocks: true,
  prioritize_critical: true,
}

const CREW_FALLBACK: Record<Department, { start: number; end: number }> = {
  Engineering: { start: 90, end: 270 },
  'S&T': { start: 120, end: 260 },
  TRD: { start: 150, end: 300 },
}

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [page, setPage] = useState<PageKey>('maintenance')
  const [section, setSection] = useState('')
  const [subsections, setSubsections] = useState<string[]>([])
  const [trains, setTrains] = useState<Train[]>([])
  const [maintenanceJobs, setMaintenanceJobs] = useState<MaintenanceJob[]>([])
  const [loadingInitial, setLoadingInitial] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [prioritizing, setPrioritizing] = useState(false)
  const [prioritized, setPrioritized] = useState(false)

  const [conditions, setConditions] = useState<Conditions | null>(null)
  const [objectives, setObjectives] = useState<Objectives>(DEFAULT_OBJECTIVES)

  const [optimizing, setOptimizing] = useState(false)
  const [optimizeResult, setOptimizeResult] = useState<OptimizeResult | null>(null)
  const [hasGenerated, setHasGenerated] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [sec, cond, trainList, jobs] = await Promise.all([
          api.getSection(),
          api.getConditions(),
          api.getTrains(),
          api.getMaintenance(),
        ])
        if (cancelled) return
        setSection(sec.section)
        setSubsections(sec.subsections)
        setConditions(cond)
        setTrains(trainList)
        setMaintenanceJobs(jobs)
      } catch (err) {
        if (!cancelled) setLoadError('Could not reach the RailMaster backend. Is it running on :8000?')
      } finally {
        if (!cancelled) setLoadingInitial(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const runPrioritization = useCallback(async () => {
    setPrioritizing(true)
    try {
      const sorted = await api.runPrioritize()
      setMaintenanceJobs(sorted)
      setPrioritized(true)
    } finally {
      setPrioritizing(false)
    }
  }, [])

  const setObjective = useCallback((key: keyof Objectives, value: boolean) => {
    setObjectives((prev) => ({ ...prev, [key]: value }))
  }, [])

  const updateBlockWindow = useCallback((field: 'start' | 'end', minutes: number) => {
    setConditions((prev) => (prev ? { ...prev, block_window: { ...prev.block_window, [field]: minutes } } : prev))
  }, [])

  const updateCrewWindow = useCallback((dept: Department, field: 'start' | 'end', minutes: number) => {
    setConditions((prev) =>
      prev
        ? {
            ...prev,
            crew_windows: {
              ...prev.crew_windows,
              [dept]: { ...prev.crew_windows[dept], [field]: minutes },
            },
          }
        : prev
    )
  }, [])

  const toggleCrewAvailable = useCallback(
    (dept: Department, available: boolean) => {
      setConditions((prev) => {
        if (!prev) return prev
        const window = available ? CREW_FALLBACK[dept] : { start: 0, end: 0 }
        return { ...prev, crew_windows: { ...prev.crew_windows, [dept]: window } }
      })
    },
    []
  )

  const setTrainDelay = useCallback((trainNumber: string, minutes: number) => {
    setConditions((prev) => {
      if (!prev) return prev
      const delays = { ...prev.train_delays }
      if (minutes === 0) delete delays[trainNumber]
      else delays[trainNumber] = minutes
      return { ...prev, train_delays: delays }
    })
  }, [])

  const setHighPriorityTrains = useCallback((trainNumbers: string[]) => {
    setConditions((prev) => (prev ? { ...prev, high_priority_trains: trainNumbers } : prev))
  }, [])

  const generatePlan = useCallback(async () => {
    if (!conditions) return
    setOptimizing(true)
    try {
      const result = await api.runOptimize({ objectives, conditions })
      setOptimizeResult(result)
      setHasGenerated(true)
    } finally {
      setOptimizing(false)
    }
  }, [conditions, objectives])

  const reoptimize = useCallback(async () => {
    if (!conditions) return
    setOptimizing(true)
    try {
      const result = await api.runReoptimize({ objectives, conditions })
      setOptimizeResult(result)
    } finally {
      setOptimizing(false)
    }
  }, [conditions, objectives])

  return (
    <AppStateContext.Provider
      value={{
        page,
        setPage,
        section,
        subsections,
        trains,
        maintenanceJobs,
        loadingInitial,
        loadError,
        prioritizing,
        prioritized,
        runPrioritization,
        conditions,
        objectives,
        setObjective,
        updateBlockWindow,
        updateCrewWindow,
        toggleCrewAvailable,
        setTrainDelay,
        setHighPriorityTrains,
        optimizing,
        optimizeResult,
        hasGenerated,
        generatePlan,
        reoptimize,
      }}
    >
      {children}
    </AppStateContext.Provider>
  )
}

export function useAppState() {
  const ctx = useContext(AppStateContext)
  if (!ctx) throw new Error('useAppState must be used within AppStateProvider')
  return ctx
}
