import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import Panel from '../components/Panel'
import Button from '../components/Button'
import ConditionPanel from '../components/ConditionPanel'
import MaintenanceTable from '../components/MaintenanceTable'
import MaintenanceDetail from '../components/MaintenanceDetail'
import TrainTable from '../components/TrainTable'
import { useAppState } from '../context/AppState'
import { MaintenanceJob } from '../types'

export default function MaintenancePortal() {
  const { section, trains, maintenanceJobs, conditions, prioritizing, prioritized, runPrioritization } =
    useAppState()
  const [selected, setSelected] = useState<MaintenanceJob | null>(null)

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-0.5">RAIL MASTER</h1>
      <p className="text-sm text-gray-500 mb-5">Maintenance Portal</p>

      <Panel className="mb-5">
        <div className="flex items-end gap-6">
          <div>
            <label className="block text-[11px] font-semibold uppercase text-gray-500 mb-1">
              Select Section
            </label>
            <select
              disabled
              className="px-2 py-1.5 border border-rail-border text-sm bg-gray-50 text-gray-700 w-56"
            >
              <option>{section}</option>
            </select>
          </div>
          <div>
            <label className="block text-[11px] font-semibold uppercase text-gray-500 mb-1">Date</label>
            <select
              disabled
              className="px-2 py-1.5 border border-rail-border text-sm bg-gray-50 text-gray-700 w-32"
            >
              <option>Today</option>
            </select>
          </div>
        </div>
      </Panel>

      {conditions && <ConditionPanel trains={trains} conditions={conditions} />}

      <Panel title={`Train Movements — ${trains.length} trains`} className="mb-5">
        <TrainTable trains={trains} />
      </Panel>

      <Panel
        title={`Maintenance Work Queue — ${maintenanceJobs.length} jobs`}
        action={
          <Button
            variant="primary"
            className="flex items-center gap-1.5"
            onClick={runPrioritization}
            disabled={prioritizing}
          >
            <Sparkles size={14} />
            {prioritizing ? 'Analyzing maintenance data...' : 'RUN AI PRIORITIZATION'}
          </Button>
        }
      >
        {prioritized && (
          <div className="text-xs text-gray-500 mb-2">
            Sorted by DCI (ML Priority Score) — highest priority first.
          </div>
        )}
        <MaintenanceTable jobs={maintenanceJobs} onSelect={setSelected} />
      </Panel>

      {selected && <MaintenanceDetail job={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
