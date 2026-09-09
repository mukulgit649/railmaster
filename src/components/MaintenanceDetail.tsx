import { ReactNode } from 'react'
import { X } from 'lucide-react'
import { MaintenanceJob } from '../types'
import { fmtMinutes } from '../utils/time'
import StatusBadge, { dciToPriority, priorityTone } from './StatusBadge'

export default function MaintenanceDetail({ job, onClose }: { job: MaintenanceJob; onClose: () => void }) {
  const priority = dciToPriority(job.dci)

  return (
    <>
      <div className="fixed inset-0 bg-black/20 z-20" onClick={onClose} />
      <div className="fixed top-0 right-0 h-full w-[380px] bg-white border-l border-rail-border shadow-lg z-30 flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-rail-border">
          <h2 className="text-sm font-bold uppercase tracking-wide text-gray-700">Maintenance Details</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800">
            <X size={18} />
          </button>
        </div>
        <div className="p-4 space-y-3 text-sm flex-1 overflow-y-auto">
          <Row label="ID" value={job.id} bold />
          <Row label="Asset" value={job.asset} />
          <Row label="Department" value={job.department} />
          <Row label="Section" value={job.section} />
          <Row label="Work" value={job.work} />
          <Row label="Duration" value={`${job.duration} min`} />
          <Row label="Required Crew" value={job.required_crew} />
          <Row label="Required Equipment" value={job.required_equipment} />
          <Row
            label="Preferred Window"
            value={`${fmtMinutes(job.preferred_start)} – ${fmtMinutes(job.preferred_end)}`}
          />
          <Row label="Status" value={<StatusBadge text={priority} tone={priorityTone(priority)} />} />
          <div className="pt-2 border-t border-rail-border">
            <div className="text-[11px] font-semibold uppercase text-gray-500 mb-1">ML Priority Score</div>
            <div className="text-2xl font-bold text-gray-900">{job.dci} / 100</div>
            <div className="text-xs text-gray-500 mt-0.5">
              DCI computed by the XGBoost priority model from asset condition, overdue days, traffic and
              failure history.
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

function Row({ label, value, bold }: { label: string; value: ReactNode; bold?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-gray-100 pb-2">
      <span className="text-gray-500 text-xs uppercase tracking-wide">{label}</span>
      <span className={bold ? 'font-semibold text-gray-900' : 'text-gray-800'}>{value}</span>
    </div>
  )
}
