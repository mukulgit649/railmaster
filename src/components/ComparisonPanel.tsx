import { OptimizeResult } from '../types'
import { fmtMinutes } from '../utils/time'
import Panel from './Panel'

export default function ComparisonPanel({ result }: { result: OptimizeResult }) {
  const manual = result.manual_baseline
  const tasks = result.included_tasks ?? []
  if (!manual || tasks.length === 0) return null

  const timeSaved = manual.total_block_time - (result.duration ?? 0)
  const disruptionReduced = manual.disruption - (result.estimated_delay ?? 0)
  const manualBlocks = manual.blocks.length

  return (
    <Panel title="Manual Approach vs. RailMaster" className="mb-5">
      <div className="grid grid-cols-2 gap-4">
        <div className="border border-rail-border p-3">
          <div className="text-[11px] font-bold uppercase tracking-wide text-gray-500 mb-2">
            Option 1 — Current Manual Approach
          </div>
          <div className="space-y-1.5">
            {manual.blocks.map((b, i) => (
              <div key={b.job_id} className="text-xs text-gray-700">
                <span className="font-semibold text-gray-900">Block {i + 1}:</span> {fmtMinutes(b.start)}–
                {fmtMinutes(b.end)} — {b.work}
              </div>
            ))}
          </div>
          <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-600 space-y-0.5">
            <div>
              Total block time: <span className="font-semibold text-gray-900">{manual.total_block_time} min</span>
            </div>
            <div>
              Estimated disruption: <span className="font-semibold text-gray-900">{manual.disruption} min</span>
            </div>
          </div>
        </div>

        <div className="border border-rail-blue bg-blue-50/40 p-3">
          <div className="text-[11px] font-bold uppercase tracking-wide text-rail-blue mb-2">
            Option 2 — RailMaster (Recommended)
          </div>
          <div className="text-sm text-gray-800">
            One consolidated block: {result.start_label} – {result.end_label}
          </div>
          <div className="mt-2 pt-2 border-t border-blue-100 text-xs text-gray-600 space-y-0.5">
            <div>
              Tasks: <span className="font-semibold text-gray-900">{tasks.length}</span>
            </div>
            <div>
              Total block time: <span className="font-semibold text-gray-900">{result.duration} min</span>
            </div>
            <div>
              Estimated disruption:{' '}
              <span className="font-semibold text-gray-900">{result.estimated_delay} min</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-rail-border grid grid-cols-3 gap-4">
        <Highlight label="Block time saved" value={`${timeSaved} min`} />
        <Highlight label="Train disruption reduced" value={`${disruptionReduced} min`} />
        <Highlight label="Maintenance tasks consolidated" value={`${manualBlocks} → 1 block`} />
      </div>

      <div className="mt-5 pt-4 border-t border-rail-border">
        <div className="text-[11px] font-bold uppercase tracking-wide text-gray-500 mb-2">
          Manual vs. Optimized
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[11px] uppercase text-gray-500 border-b border-rail-border">
              <th className="py-1.5 pr-2 font-semibold"></th>
              <th className="py-1.5 pr-2 font-semibold text-right">Manual</th>
              <th className="py-1.5 pr-2 font-semibold text-right">RailMaster</th>
            </tr>
          </thead>
          <tbody>
            <ComparisonRow label="Maintenance blocks" manual={manualBlocks} optimized={1} />
            <ComparisonRow label="Block duration" manual={`${manual.total_block_time} min`} optimized={`${result.duration} min`} />
            <ComparisonRow label="Train disruption" manual={`${manual.disruption} min`} optimized={`${result.estimated_delay} min`} />
            <ComparisonRow label="Tasks completed" manual={tasks.length} optimized={tasks.length} />
            <ComparisonRow
              label="Resource conflicts"
              manual={manual.affected_trains.length > 0 ? 1 : 0}
              optimized={result.train_conflicts ?? 0}
            />
          </tbody>
        </table>
      </div>

      <p className="text-[11px] text-gray-400 italic mt-3">
        Illustrative results generated from synthetic data.
      </p>
    </Panel>
  )
}

function Highlight({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-lg font-bold text-rail-green">{value}</div>
      <div className="text-[11px] text-gray-500 mt-0.5">{label}</div>
    </div>
  )
}

function ComparisonRow({
  label,
  manual,
  optimized,
}: {
  label: string
  manual: string | number
  optimized: string | number
}) {
  return (
    <tr className="border-b border-gray-100 last:border-0">
      <td className="py-1.5 pr-2 text-gray-700">{label}</td>
      <td className="py-1.5 pr-2 text-right text-gray-700">{manual}</td>
      <td className="py-1.5 pr-2 text-right font-semibold text-gray-900">{optimized}</td>
    </tr>
  )
}
