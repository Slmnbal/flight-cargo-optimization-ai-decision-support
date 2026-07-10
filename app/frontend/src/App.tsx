import { Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { OverviewPage } from '@/pages/OverviewPage'
import { RoutesPage } from '@/pages/RoutesPage'
import { FlightsPage } from '@/pages/FlightsPage'
import { CargoRequestsPage } from '@/pages/CargoRequestsPage'
import { OptimizePage } from '@/pages/OptimizePage'
import { AgentPage } from '@/pages/AgentPage'

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<OverviewPage />} />
        <Route path="routes" element={<RoutesPage />} />
        <Route path="flights" element={<FlightsPage />} />
        <Route path="cargo-requests" element={<CargoRequestsPage />} />
        <Route path="optimize" element={<OptimizePage />} />
        <Route path="agent" element={<AgentPage />} />
      </Route>
    </Routes>
  )
}

export default App
