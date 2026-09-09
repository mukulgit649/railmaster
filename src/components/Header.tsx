export default function Header() {
  return (
    <header className="h-14 shrink-0 bg-white border-b border-rail-border flex items-center justify-between px-4">
      <div className="flex items-baseline gap-3">
        <span className="text-lg font-bold tracking-tight text-gray-900">RAIL MASTER</span>
        <span className="text-xs text-gray-500 hidden sm:inline">
          AI-Assisted Railway Maintenance Block Planner
        </span>
      </div>
      <div className="flex items-center gap-5 text-sm">
        <span className="flex items-center gap-1.5 text-rail-yellow font-medium">
          <span className="w-2 h-2 rounded-full bg-rail-yellow inline-block" />
          SIMULATION MODE
        </span>
        <span className="text-gray-600 border-l border-rail-border pl-5">OMC Dispatcher</span>
      </div>
    </header>
  )
}
