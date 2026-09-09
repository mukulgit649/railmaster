import { Train } from '../types'
import StatusBadge, { trainPriorityTone } from './StatusBadge'

export default function TrainTable({ trains }: { trains: Train[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-rail-border text-left text-[11px] uppercase text-gray-500">
          <th className="py-1.5 pr-2 font-semibold">Train</th>
          <th className="py-1.5 pr-2 font-semibold">Type</th>
          <th className="py-1.5 pr-2 font-semibold">Entry</th>
          <th className="py-1.5 pr-2 font-semibold">Exit</th>
          <th className="py-1.5 pr-2 font-semibold">Section</th>
          <th className="py-1.5 pr-2 font-semibold">Priority</th>
          <th className="py-1.5 pr-2 font-semibold">Status</th>
        </tr>
      </thead>
      <tbody>
        {trains.map((t) => (
          <tr key={t.number} className="border-b border-gray-100 last:border-0">
            <td className="py-2 pr-2 font-mono font-medium text-gray-900">{t.number}</td>
            <td className="py-2 pr-2 text-gray-700">{t.type}</td>
            <td className="py-2 pr-2 text-gray-700">{t.entry}</td>
            <td className="py-2 pr-2 text-gray-700">{t.exit}</td>
            <td className="py-2 pr-2 text-gray-700">{t.section}</td>
            <td className="py-2 pr-2">
              <StatusBadge text={t.priority} tone={trainPriorityTone(t.priority)} />
            </td>
            <td className="py-2 pr-2 text-gray-700">{t.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
