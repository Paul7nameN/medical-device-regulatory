import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { DashboardPage } from '@/pages/Dashboard'
import { HistoryPage } from '@/pages/History'
import { AnalysisProvider } from '@/lib/context/AnalysisContext'
import { ThemeProvider } from '@/lib/context/ThemeContext'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
})

export function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AnalysisProvider>
          <BrowserRouter>
            <Layout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/upload" element={<Navigate to="/" replace />} />
                <Route path="/violations" element={<Navigate to="/" replace />} />
                <Route path="/temperature" element={<Navigate to="/" replace />} />
                <Route path="/reports" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </BrowserRouter>
        </AnalysisProvider>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export default App
