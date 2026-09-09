import { OptimizeResult, Train } from '../types'
import { fmtMinutes, parseHM } from '../utils/time'

const DAY_START = 0 // 00:00
const DAY_END = 360 // 06:00

function pct(minutes: number) {
  const clamped = Math.max(DAY_START, Math.min(DAY_END, minutes))
  return ((clamped - DAY_START) / (DAY_END - DAY_START)) * 100
}

const AXIS = [0, 60, 120, 180, 240, 300, 360]

export default function Timeline({ trains, result }: { trains: Train[]; result: OptimizeResult }) {
  const includedTasks = result.included_tasks ?? []
  const blockStart = result.start ?? 0

  return (
    <div className="pt-2">
      <div className="flex text-[11px] text-gray-500 font-mono mb-2 pl-28">
        {AXIS.map((m) => (
          <div key={m} className="flex-1">
            {fmtMinutes(m)}
          </div>
        ))}
      </div>

      <div className="space-y-1.5 max-h-[420px] overflow-y-auto pr-1">
        {trains.map((t) => {
          const entry = parseHM(t.entry)
          const exit = parseHM(t.exit)
          const affected = (result.trains_affected ?? []).includes(t.number)
          return (
            <div key={t.number} className="flex items-center">
              <div className="w-28 shrink-0 text-xs text-gray-700 font-medium truncate">Train {t.number}</div>
              <div className="flex-1 relative h-3.5 bg-gray-50 border border-gray-100">
                <div
                  className={`absolute top-0 h-full ${
                    t.priority === 'HIGH' ? 'bg-rail-blue' : affected ? 'bg-orange-400' : 'bg-blue-200'
                  }`}
                  style={{ left: `${pct(entry)}%`, width: `${Math.max(0.4, pct(exit) - pct(entry))}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>

      {includedTasks.length > 0 && (
        <div className="mt-3 pt-3 border-t border-rail-border space-y-1.5">
          {includedTasks.map((task) => {
            const start = blockStart
            const end = blockStart + (result.duration ?? 0)
            // Each task finishes at its own duration inside the shared block window
            // (parallel crews); the block itself spans the longest included task.
            return (
              <div key={task.id} className="flex items-center">
                <div className="w-28 shrink-0 text-xs text-gray-700 font-medium truncate">{task.work}</div>
                <div className="flex-1 relative h-3.5 bg-gray-50 border border-gray-100">
                  <div
                    className="absolute top-0 h-full bg-rail-green"
                    style={{ left: `${pct(start)}%`, width: `${Math.max(0.4, pct(end) - pct(start))}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="flex items-center gap-4 mt-4 pt-3 border-t border-rail-border text-xs text-gray-600">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 bg-rail-blue inline-block" /> High-priority train
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 bg-orange-400 inline-block" /> Normal train (affected)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 bg-blue-200 inline-block" /> Normal train
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 bg-rail-green inline-block" /> Maintenance block
        </span>
      </div>
    </div>
  )
}
