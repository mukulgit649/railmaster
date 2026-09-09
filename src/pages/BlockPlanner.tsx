import { useEffect, useRef, useState } from 'react'
import { Check, Loader2 } from 'lucide-react'
import Panel from '../components/Panel'
import Button from '../components/Button'
import Timeline from '../components/Timeline'
import OptimizationResult from '../components/OptimizationResult'
import ComparisonPanel from '../components/ComparisonPanel'
import ExplanationPanel from '../components/ExplanationPanel'
import { useAppState } from '../context/AppState'
import { Department } from '../types'
import { fmtMinutes, parseHM } from '../utils/time'

const LOADING_STEPS = [
  { label: 'Loading train timetable...', done: (n: number) => `✓ ${n} trains loaded` },
  { label: 'Loading maintenance tasks...', done: (n: number) => `✓ ${n} tasks loaded` },
  { label: 'Checking crew availability...', done: () => '✓ Resources checked' },
  { label: 'Checking operational constraints...', done: () => '✓ Constraints checked' },
  { label: 'Running maintenance prioritization...', done: () => '✓ Priority scores generated' },
  { label: 'Running block optimization...', done: () => '✓ Block optimization complete' },
  { label: 'Checking conflicts...', done: () => '✓ Conflict analysis complete' },
]

const DEPARTMENTS: Department[] = ['Engineering', 'S&T', 'TRD']

export default function BlockPlanner() {
  const {
    section,
    subsections,
    trains,
    maintenanceJobs,
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
  } = useAppState()

  const [showLoading, setShowLoading] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const [changeNote, setChangeNote] = useState<string | null>(null)
  const [showUpdatedBanner, setShowUpdatedBanner] = useState(false)
  const timerRef = useRef<number | null>(null)

  const [delayTrain, setDelayTrain] = useState(trains[0]?.number ?? '')
  const [delayMinutes, setDelayMinutes] = useState(0)

  useEffect(() => {
    if (!delayTrain && trains.length) setDelayTrain(trains[0].number)
  }, [trains, delayTrain])

  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current)
    }
  }, [])

  const runLoadingSequence = (onDone: () => void) => {
    setShowLoading(true)
    setStepIndex(0)
    const advance = (i: number) => {
      timerRef.current = window.setTimeout(() => {
        if (i < LOADING_STEPS.length - 1) {
          setStepIndex(i + 1)
          advance(i + 1)
        } else {
          timerRef.current = window.setTimeout(() => {
            setShowLoading(false)
            onDone()
          }, 400)
        }
      }, 380)
    }
    advance(0)
  }

  const handleGenerate = () => {
    setShowUpdatedBanner(false)
    generatePlan()
    runLoadingSequence(() => {})
  }

  const handleReoptimize = () => {
    setShowUpdatedBanner(true)
    reoptimize()
    runLoadingSequence(() => {})
  }

  const note = (text: string) => setChangeNote(text)

  if (!conditions) return null

  return (
    <div className="p-6 max-w-[1100px] mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-0.5">Block Planner</h1>
      <p className="text-sm text-gray-500 mb-5">
        Generate an optimized maintenance block for the selected section.
      </p>

      <Panel title="Selected Section" className="mb-5">
        <div className="flex items-center gap-6">
          <div className="text-lg font-bold text-gray-900">{section}</div>
          <div className="flex gap-1.5">
            {subsections.map((s) => (
              <span key={s} className="px-2 py-0.5 text-xs border border-rail-border bg-gray-50 text-gray-600">
                {s}
              </span>
            ))}
          </div>
        </div>
      </Panel>

      <Panel title="Current Conditions" className="mb-5">
        <div className="grid grid-cols-4 gap-4">
          <Stat label="Train Movements" value={`${trains.length} trains`} />
          <Stat label="Maintenance Tasks" value={`${maintenanceJobs.length} jobs`} />
          <Stat label="Available Window" value={`${fmtMinutes(conditions.block_window.start)}–${fmtMinutes(conditions.block_window.end)}`} />
          <Stat
            label="Available Crews"
            value={DEPARTMENTS.filter((d) => conditions.crew_windows[d].end > conditions.crew_windows[d].start).join(', ') || 'None'}
          />
        </div>
      </Panel>

      <Panel title="Optimization Objectives" className="mb-5">
        <div className="flex flex-wrap gap-5">
          <ObjectiveCheckbox
            label="Maximize maintenance completed"
            checked={objectives.maximize_completed}
            onChange={(v) => setObjective('maximize_completed', v)}
          />
          <ObjectiveCheckbox
            label="Minimize train disruption"
            checked={objectives.minimize_disruption}
            onChange={(v) => setObjective('minimize_disruption', v)}
          />
          <ObjectiveCheckbox
            label="Minimize number of blocks"
            checked={objectives.minimize_blocks}
            onChange={(v) => setObjective('minimize_blocks', v)}
          />
          <ObjectiveCheckbox
            label="Prioritize critical maintenance"
            checked={objectives.prioritize_critical}
            onChange={(v) => setObjective('prioritize_critical', v)}
          />
        </div>
        <div className="mt-4 pt-4 border-t border-rail-border">
          <Button variant="primary" onClick={handleGenerate} disabled={optimizing || showLoading}>
            {optimizing || showLoading ? 'Generating...' : 'GENERATE OPTIMAL BLOCK PLAN'}
          </Button>
        </div>
      </Panel>

      {showLoading && (
        <Panel className="mb-5">
          <div className="space-y-2">
            {LOADING_STEPS.map((step, i) => (
              <div key={step.label} className="flex items-center gap-2 text-sm">
                {i < stepIndex ? (
                  <Check size={15} className="text-rail-green" />
                ) : i === stepIndex ? (
                  <Loader2 size={15} className="text-rail-blue animate-spin" />
                ) : (
                  <span className="w-[15px] h-[15px] inline-block" />
                )}
                <span className={i <= stepIndex ? 'text-gray-800' : 'text-gray-400'}>
                  {i < stepIndex
                    ? step.done(step.label.includes('train') ? trains.length : maintenanceJobs.length)
                    : step.label}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {showUpdatedBanner && !showLoading && optimizeResult && (
        <Panel className="mb-5 border-l-4 !border-l-rail-blue">
          <div className="text-sm">
            <span className="font-bold text-rail-blue uppercase tracking-wide text-xs mr-2">Plan Updated</span>
            {changeNote && <span className="text-gray-700">Reason: {changeNote}</span>}
          </div>
        </Panel>
      )}

      {hasGenerated && !showLoading && optimizeResult && (
        <>
          <OptimizationResult result={optimizeResult} />
          <Panel title="Timeline" className="mb-5">
            <Timeline trains={trains} result={optimizeResult} />
          </Panel>
          <ComparisonPanel result={optimizeResult} />
          <ExplanationPanel result={optimizeResult} />
        </>
      )}

      <Panel title="Change Conditions">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-[11px] font-semibold uppercase text-gray-500 mb-1">
              Delay a train
            </label>
            <div className="flex gap-2">
              <select
                value={delayTrain}
                onChange={(e) => setDelayTrain(e.target.value)}
                className="px-2 py-1.5 border border-rail-border text-sm bg-white flex-1"
              >
                {trains.map((t) => (
                  <option key={t.number} value={t.number}>
                    Train {t.number}
                  </option>
                ))}
              </select>
              <select
                value={delayMinutes}
                onChange={(e) => {
                  const mins = Number(e.target.value)
                  setDelayMinutes(mins)
                  setTrainDelay(delayTrain, mins)
                  note(mins > 0 ? `Train ${delayTrain} delayed by ${mins} min.` : `Train ${delayTrain} delay cleared.`)
                }}
                className="px-2 py-1.5 border border-rail-border text-sm bg-white w-28"
              >
                {[0, 5, 10, 15, 20, 30, 45].map((m) => (
                  <option key={m} value={m}>
                    {m} min
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold uppercase text-gray-500 mb-1">
              Block window
            </label>
            <div className="flex gap-2 items-center">
              <input
                type="text"
                defaultValue={fmtMinutes(conditions.block_window.start)}
                onBlur={(e) => {
                  updateBlockWindow('start', parseHM(e.target.value))
                  note(`Block window start changed to ${e.target.value}.`)
                }}
                className="px-2 py-1.5 border border-rail-border text-sm w-24 font-mono"
              />
              <span className="text-gray-400">–</span>
              <input
                type="text"
                defaultValue={fmtMinutes(conditions.block_window.end)}
                onBlur={(e) => {
                  updateBlockWindow('end', parseHM(e.target.value))
                  note(`Block window end changed to ${e.target.value}.`)
                }}
                className="px-2 py-1.5 border border-rail-border text-sm w-24 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold uppercase text-gray-500 mb-1">
              Crew availability
            </label>
            <div className="flex gap-4 pt-1">
              {DEPARTMENTS.map((d) => {
                const available = conditions.crew_windows[d].end > conditions.crew_windows[d].start
                return (
                  <label key={d} className="flex items-center gap-1.5 text-sm text-gray-800">
                    <input
                      type="checkbox"
                      checked={available}
                      onChange={(e) => {
                        toggleCrewAvailable(d, e.target.checked)
                        note(`${d} crew marked ${e.target.checked ? 'available' : 'unavailable'}.`)
                      }}
                      className="accent-rail-blue"
                    />
                    {d}
                  </label>
                )
              })}
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold uppercase text-gray-500 mb-1">
              High-priority trains
            </label>
            <div className="flex flex-wrap gap-2 pt-1 max-h-20 overflow-y-auto">
              {trains.map((t) => {
                const checked = conditions.high_priority_trains.includes(t.number)
                return (
                  <label
                    key={t.number}
                    className="flex items-center gap-1 text-xs border border-rail-border px-1.5 py-0.5 bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        const next = e.target.checked
                          ? [...conditions.high_priority_trains, t.number]
                          : conditions.high_priority_trains.filter((n) => n !== t.number)
                        setHighPriorityTrains(next)
                        note(`Train ${t.number} marked ${e.target.checked ? 'high-priority' : 'normal'}.`)
                      }}
                      className="accent-rail-blue"
                    />
                    {t.number}
                  </label>
                )
              })}
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-rail-border">
          <Button variant="primary" onClick={handleReoptimize} disabled={optimizing || showLoading || !hasGenerated}>
            {optimizing || showLoading ? 'Re-optimizing...' : 'RE-OPTIMIZE'}
          </Button>
          {!hasGenerated && (
            <span className="ml-3 text-xs text-gray-500">Generate a plan first, then adjust conditions here.</span>
          )}
        </div>
      </Panel>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-base font-bold text-gray-900 mt-0.5">{value}</div>
    </div>
  )
}

function ObjectiveCheckbox({
  label,
  checked,
  onChange,
}: {
  label: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <label className="flex items-center gap-1.5 text-sm text-gray-800">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="accent-rail-blue"
      />
      {label}
    </label>
  )
}
