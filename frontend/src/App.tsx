import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Notifications } from '@mantine/notifications'
import '@mantine/notifications/styles.css'
import { AppLayout } from './components/AppLayout'
import { Dashboard } from './pages/Dashboard'
import { TestList } from './pages/TestList'
import { TestViewer } from './pages/TestViewer'
import { TestReviewEdit } from './pages/TestReviewEdit'
import { Upload } from './pages/Upload'

export default function App() {
  return (
    <>
      <Notifications />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="upload" element={<Upload />} />
            <Route path="tests" element={<TestList />} />
            <Route path="tests/:id" element={<TestViewer />} />
            <Route path="tests/:id/review" element={<TestReviewEdit />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  )
}
