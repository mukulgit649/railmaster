import { MaintenanceJob } from '../types'
import StatusBadge, { dciToPriority, priorityTone } from './StatusBadge'

export default function MaintenanceTable({
  jobs,
  onSelect,
}: {
  jobs: MaintenanceJob[]
  onSelect: (job: MaintenanceJob) => void
}) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-rail-border text-left text-[11px] uppercase text-gray-500">
          <th className="py-1.5 pr-2 font-semibold w-10">Pri.</th>
          <th className="py-1.5 pr-2 font-semibold">ID</th>
          <th className="py-1.5 pr-2 font-semibold">Asset</th>
          <th className="py-1.5 pr-2 font-semibold">Department</th>
          <th className="py-1.5 pr-2 font-semibold">Section</th>
          <th className="py-1.5 pr-2 font-semibold">Work</th>
          <th className="py-1.5 pr-2 font-semibold">Duration</th>
          <th className="py-1.5 pr-2 font-semibold">DCI</th>
          <th className="py-1.5 pr-2 font-semibold">Status</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((job, i) => (
          <tr
            key={job.id}
            onClick={() => onSelect(job)}
            className="border-b border-gray-100 last:border-0 cursor-pointer hover:bg-blue-50/40"
          >
            <td className="py-2 pr-2 text-gray-700">{i + 1}</td>
            <td className="py-2 pr-2 font-mono text-gray-700">{job.id}</td>
            <td className="py-2 pr-2 font-medium text-gray-900">{job.asset}</td>
            <td className="py-2 pr-2 text-gray-700">{job.department}</td>
            <td className="py-2 pr-2 text-gray-700">{job.section}</td>
            <td className="py-2 pr-2 text-gray-700">{job.work}</td>
            <td className="py-2 pr-2 text-gray-700">{job.duration} min</td>
            <td className="py-2 pr-2 font-mono text-gray-700">{job.dci}</td>
            <td className="py-2 pr-2">
              <StatusBadge text={dciToPriority(job.dci)} tone={priorityTone(dciToPriority(job.dci))} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
