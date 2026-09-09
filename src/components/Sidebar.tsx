import { Wrench, CalendarClock } from 'lucide-react'
import { PageKey } from '../types'
import { useAppState } from '../context/AppState'

const NAV: { key: PageKey; label: string; icon: React.ElementType }[] = [
  { key: 'maintenance', label: 'Maintenance', icon: Wrench },
  { key: 'planner', label: 'Block Planner', icon: CalendarClock },
]

export default function Sidebar() {
  const { page, setPage } = useAppState()

  return (
    <aside className="w-[220px] shrink-0 bg-white border-r border-rail-border flex flex-col">
      <nav className="flex-1 py-2">
        {NAV.map(({ key, label, icon: Icon }) => {
          const active = page === key
          return (
            <button
              key={key}
              onClick={() => setPage(key)}
              className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-left border-l-[3px] ${
                active
                  ? 'border-rail-blue bg-blue-50 text-rail-blue font-semibold'
                  : 'border-transparent text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Icon size={16} strokeWidth={2} />
              {label}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
