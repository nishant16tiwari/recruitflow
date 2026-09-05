import { Navigate, Route, Routes } from 'react-router-dom'
import { ToastProvider } from '@/components/Toast'
import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ApplicationsPage } from '@/pages/ApplicationsPage'
import { ApplicationDetailPage } from '@/pages/ApplicationDetailPage'
import { JobsPage } from '@/pages/JobsPage'
import { AlertsPage } from '@/pages/AlertsPage'
import { MyInterviewsPage } from '@/pages/MyInterviewsPage'

function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<ProtectedRoute requireRole="RECRUITER"><DashboardPage /></ProtectedRoute>} />
          <Route path="/applications" element={<ProtectedRoute requireRole="RECRUITER"><ApplicationsPage /></ProtectedRoute>} />
          <Route path="/applications/:id" element={<ApplicationDetailPage />} />
          <Route path="/jobs" element={<ProtectedRoute requireRole="RECRUITER"><JobsPage /></ProtectedRoute>} />
          <Route path="/alerts" element={<ProtectedRoute requireRole="RECRUITER"><AlertsPage /></ProtectedRoute>} />
          <Route path="/my-interviews" element={<ProtectedRoute requireRole="INTERVIEWER"><MyInterviewsPage /></ProtectedRoute>} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </ToastProvider>
  )
}

export default App
