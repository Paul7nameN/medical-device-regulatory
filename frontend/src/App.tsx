import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { DashboardPage } from '@/pages/Dashboard'
import { HistoryPage } from '@/pages/History'
import { LiveTransportPage } from '@/pages/LiveTransport'
import { AnalysisProvider } from '@/lib/context/AnalysisContext'
import { LiveTransportProvider } from '@/lib/context/LiveTransportContext'
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
            <LiveTransportProvider>
              <Layout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/live" element={<LiveTransportPage />} />
                  <Route path="/history" element={<HistoryPage />} />
                  <Route path="/upload" element={<Navigate to="/" replace />} />
                  <Route path="/violations" element={<Navigate to="/" replace />} />
                  <Route path="/temperature" element={<Navigate to="/" replace />} />
                  <Route path="/reports" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            </LiveTransportProvider>
          </BrowserRouter>
        </AnalysisProvider>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export default App
