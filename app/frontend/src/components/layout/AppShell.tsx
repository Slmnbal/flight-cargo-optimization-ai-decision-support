import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col bg-surface-alt">
      {/* İnce kırmızı marka şeridi -- kırmızı burada sadece bir "vurgu
          çizgisi", chrome (sidebar/header) lacivert kalıyor. */}
      <div className="h-1 w-full shrink-0 bg-brand" />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <main className="flex-1 overflow-y-auto p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
