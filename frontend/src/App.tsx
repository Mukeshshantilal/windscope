import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { AccuracyPage } from '@/pages/AccuracyPage'
import { ExplorerPage } from '@/pages/ExplorerPage'
import { GenerationPage } from '@/pages/GenerationPage'
import { MethodologyPage } from '@/pages/MethodologyPage'
import { OverviewPage } from '@/pages/OverviewPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/generation" element={<GenerationPage />} />
        <Route path="/accuracy" element={<AccuracyPage />} />
        <Route path="/explorer" element={<ExplorerPage />} />
        <Route path="/methodology" element={<MethodologyPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
