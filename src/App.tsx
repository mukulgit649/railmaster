import { AppStateProvider, useAppState } from './context/AppState'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import MaintenancePortal from './pages/MaintenancePortal'
import BlockPlanner from './pages/BlockPlanner'

function Main() {
  const { page, loadingInitial, loadError } = useAppState()

  return (
    <div className="h-screen flex flex-col">
      <Header />
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        <main className="flex-1 min-w-0 overflow-y-auto bg-rail-bg">
          {loadError ? (
            <div className="p-6 max-w-lg mx-auto mt-16 bg-white border border-rail-red text-sm text-gray-800 p-4">
              <div className="font-semibold text-rail-red mb-1">Backend unavailable</div>
              {loadError}
            </div>
          ) : loadingInitial ? (
            <div className="p-6 text-sm text-gray-500">Loading section data...</div>
          ) : (
            <>
              {page === 'maintenance' && <MaintenancePortal />}
              {page === 'planner' && <BlockPlanner />}
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AppStateProvider>
      <Main />
    </AppStateProvider>
  )
}
