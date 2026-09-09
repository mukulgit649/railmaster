import { Check, X } from 'lucide-react'
import { Conditions, Train } from '../types'
import { fmtMinutes } from '../utils/time'
import Panel from './Panel'

export default function ConditionPanel({ trains, conditions }: { trains: Train[]; conditions: Conditions }) {
  const highCount = trains.filter((t) => t.priority === 'HIGH').length
  const departments: (keyof typeof conditions.crew_windows)[] = ['Engineering', 'S&T', 'TRD']

  return (
    <Panel title="Operating Conditions" className="mb-5">
      <div className="grid grid-cols-4 gap-3">
        <div className="border border-rail-border px-3 py-2.5">
          <div className="text-[11px] font-semibold uppercase text-gray-500">Train Operations</div>
          <div className="text-lg font-bold text-gray-900 mt-1">{trains.length} trains</div>
          <div className="text-xs text-gray-500 mt-0.5">{highCount} high-priority</div>
        </div>

        <div className="border border-rail-border px-3 py-2.5">
          <div className="text-[11px] font-semibold uppercase text-gray-500">Crew Availability</div>
          <div className="mt-1 space-y-0.5">
            {departments.map((d) => {
              const w = conditions.crew_windows[d]
              const available = w.end > w.start
              return (
                <div key={d} className="flex items-center gap-1.5 text-sm">
                  {available ? (
                    <Check size={13} className="text-rail-green" />
                  ) : (
                    <X size={13} className="text-rail-red" />
                  )}
                  <span className={available ? 'text-gray-800' : 'text-gray-400 line-through'}>{d}</span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="border border-rail-border px-3 py-2.5">
          <div className="text-[11px] font-semibold uppercase text-gray-500">Available Work Window</div>
          <div className="text-lg font-bold text-gray-900 mt-1">
            {fmtMinutes(conditions.block_window.start)} – {fmtMinutes(conditions.block_window.end)}
          </div>
        </div>

        <div className="border border-rail-border px-3 py-2.5">
          <div className="text-[11px] font-semibold uppercase text-gray-500">Restrictions</div>
          <div className="text-sm text-gray-800 mt-1">High-priority trains cannot be delayed.</div>
          {conditions.high_priority_trains.length > 0 && (
            <div className="text-xs text-gray-500 mt-1">{conditions.high_priority_trains.join(', ')}</div>
          )}
        </div>
      </div>
    </Panel>
  )
}
