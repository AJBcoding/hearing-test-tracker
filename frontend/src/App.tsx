import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { Dashboard } from './pages/Dashboard'
import { TestList } from './pages/TestList'
import { TestViewer } from './pages/TestViewer'
import { TestReviewEdit } from './pages/TestReviewEdit'
import { UploadForm } from './components/UploadForm'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="upload" element={<UploadForm />} />
          <Route path="tests" element={<TestList />} />
          <Route path="tests/:id" element={<TestViewer />} />
          <Route path="tests/:id/review" element={<TestReviewEdit />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
