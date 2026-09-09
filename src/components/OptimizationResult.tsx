import { Check } from 'lucide-react'
import { OptimizeResult } from '../types'
import Panel from './Panel'

export default function OptimizationResult({ result }: { result: OptimizeResult }) {
  if (!result.feasible) {
    return (
      <Panel title="Recommended Block" className="mb-5">
        <p className="text-sm text-gray-600">
          No feasible block was found under the current conditions. Try widening the block window or
          relaxing a crew constraint.
        </p>
      </Panel>
    )
  }

  const tasks = result.included_tasks ?? []

  return (
    <Panel title="Recommended Block" className="mb-5">
      <div className="grid grid-cols-6 gap-4">
        <Stat label="Section" value={result.section ?? '—'} />
        <Stat label="Time" value={`${result.start_label} – ${result.end_label}`} />
        <Stat label="Duration" value={`${result.duration} minutes`} />
        <Stat label="Maintenance Tasks" value={String(tasks.length)} />
        <Stat label="Train Conflicts" value={String(result.train_conflicts ?? 0)} />
        <Stat label="Trains Affected" value={String((result.trains_affected ?? []).length)} />
      </div>
      <div className="mt-3 text-sm text-gray-700">
        Estimated delay:{' '}
        <span className="font-semibold text-gray-900">{result.estimated_delay} minute(s)</span>
      </div>

      {tasks.length > 0 && (
        <div className="mt-4 pt-4 border-t border-rail-border">
          <div className="text-[11px] font-bold uppercase tracking-wide text-gray-500 mb-2">
            Combined Work — One Block Instead of {tasks.length} Separate Ones
          </div>
          <div className="space-y-1">
            {tasks.map((t) => (
              <div key={t.id} className="flex items-center gap-2 text-sm text-gray-800">
                <Check size={14} className="text-rail-green" />
                <span className="font-mono text-xs text-gray-500">{t.id}</span>
                {t.asset} — {t.work}
                <span className="text-xs text-gray-400 ml-auto font-mono">DCI {t.dci}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Panel>
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
