# Deep Dive: Frontend Initialization, Dashboard, and TestViewer Flows

**Combined Analysis:** Frontend user-facing flows with shared systemic issues
**Files:**
- Frontend Init: `frontend/src/App.tsx`, `frontend/src/main.tsx`
- Dashboard: `frontend/src/pages/Dashboard.tsx`
- TestViewer: `frontend/src/pages/TestViewer.tsx`

**Severity Summary:**
- Frontend Initialization: 2 High + 4 Medium + 1 Low = 7 issues
- Dashboard: 2 High + 3 Medium + 2 Low = 7 issues
- TestViewer: 2 High + 4 Medium + 2 Low = 8 issues
- **Total: 6 High + 11 Medium + 5 Low = 22 issues**

---

## Systemic Issues (All Three Flows)

### Issue 1: No Error Boundaries (Application-Wide)

**Severity:** 🔴 CRITICAL (High)
**Location:**
- `frontend/src/App.tsx:11-29` (no ErrorBoundary wrapper)
- `frontend/src/main.tsx:10-17` (no root ErrorBoundary)
- `frontend/src/pages/Dashboard.tsx` (no local ErrorBoundary)
- `frontend/src/pages/TestViewer.tsx` (no local ErrorBoundary)

**Category:** Error Handling / Reliability

**Description:**

No React Error Boundaries anywhere in the application. Any uncaught error in component rendering will crash the entire app, showing users a blank white screen with no explanation or recovery option.

**Current Code:**

```tsx
// App.tsx - No ErrorBoundary!
export default function App() {
  return (
    <>
      <Notifications />
      <BrowserRouter>
        <Routes>
          {/* If any component crashes, entire app crashes */}
          <Route path="/" element={<AppLayout />}>
            {/* ... routes */}
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  )
}

// main.tsx - No ErrorBoundary at root either!
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider>
        <App />  {/* Entire app can crash */}
      </MantineProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
```

**Impact:**
- White screen of death on any component error
- Users lose all context and data
- No way to recover without page refresh
- Poor debugging experience
- Looks unprofessional

**Solution:**

```tsx
// components/ErrorBoundary.tsx
import { Component, ReactNode } from 'react'
import { Container, Title, Text, Button, Alert, Code, Stack } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to error reporting service (Sentry, etc.)
    console.error('ErrorBoundary caught:', error, errorInfo)

    // Call optional error handler
    this.props.onError?.(error, errorInfo)

    // TODO: Send to error tracking service
    // Sentry.captureException(error, { extra: errorInfo })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined })
    window.location.href = '/dashboard' // Safe reset to known state
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <Container size="sm" py="xl">
          <Alert
            icon={<IconAlertTriangle size={24} />}
            title="Something Went Wrong"
            color="red"
            variant="filled"
            mb="xl"
          >
            <Text>
              The application encountered an unexpected error.
              Don't worry, your data is safe.
            </Text>
          </Alert>

          <Stack gap="md">
            <div>
              <Text size="sm" fw={500} mb="xs">Error Details:</Text>
              <Code block>
                {this.state.error?.message || 'Unknown error'}
              </Code>
            </div>

            <Button onClick={this.handleReset} size="lg">
              Return to Dashboard
            </Button>

            <Button
              variant="subtle"
              onClick={() => window.location.reload()}
            >
              Refresh Page
            </Button>
          </Stack>
        </Container>
      )
    }

    return this.props.children
  }
}

// App.tsx - Wrap entire app
export default function App() {
  return (
    <ErrorBoundary>  {/* Root-level error boundary */}
      <Notifications />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            {/* Feature-level error boundaries for better UX */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={
              <ErrorBoundary fallback={<DashboardErrorFallback />}>
                <Dashboard />
              </ErrorBoundary>
            } />
            <Route path="tests/:id" element={
              <ErrorBoundary fallback={<TestViewerErrorFallback />}>
                <TestViewer />
              </ErrorBoundary>
            } />
            {/* ... other routes */}
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

// Feature-specific error fallbacks
function DashboardErrorFallback() {
  return (
    <Container>
      <Alert color="red" title="Dashboard Error">
        <Text mb="md">Unable to load dashboard. Please try refreshing.</Text>
        <Button onClick={() => window.location.reload()}>Refresh</Button>
      </Alert>
    </Container>
  )
}
```

- **Pro:** Prevents entire app crashes
- **Pro:** User-friendly error messages
- **Pro:** Recovery options (reset, refresh)
- **Pro:** Can integrate error tracking (Sentry)
- **Pro:** Feature-level boundaries isolate failures

---

### Issue 2: No Error State Handling in Data Fetching

**Severity:** 🔴 CRITICAL (High)
**Location:**
- `frontend/src/pages/Dashboard.tsx:8-11` (missing isError)
- `frontend/src/pages/TestViewer.tsx:14-18` (missing isError)

**Category:** Error Handling / UX

**Description:**

Both Dashboard and TestViewer use `useQuery` but only destructure `data` and `isLoading`, completely ignoring `isError` and `error`. When API calls fail, components remain in loading state forever.

**Current Code:**

```tsx
// Dashboard.tsx
const { data: tests = [], isLoading } = useQuery({
  queryKey: ['tests'],
  queryFn: listTests
  // Missing: isError, error
})

if (isLoading) {
  return <Container><Text>Loading...</Text></Container>
}

// If API fails, stays in loading state FOREVER!

// TestViewer.tsx - same issue
const { data: test, isLoading } = useQuery({
  queryKey: ['test', id],
  queryFn: () => getTest(id!),
  enabled: !!id
  // Missing: isError, error
})
```

**Impact:**
- Users stuck on "Loading..." forever
- No indication what went wrong
- No retry mechanism
- Difficult to debug issues
- Poor user experience

**Solution:**

```tsx
// Dashboard.tsx
import { Alert, Loader, Center } from '@mantine/core'

export function Dashboard() {
  const navigate = useNavigate()

  const {
    data: tests = [],
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ['tests'],
    queryFn: listTests,
    retry: 3,  // Retry failed requests
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  // Loading state
  if (isLoading) {
    return (
      <Container>
        <Center h={200}>
          <Loader size="lg" />
        </Center>
      </Container>
    )
  }

  // Error state
  if (isError) {
    return (
      <Container size="md" py="xl">
        <Alert
          color="red"
          title="Failed to Load Tests"
          icon={<IconAlertTriangle size={20} />}
        >
          <Text mb="md">
            {error instanceof Error ? error.message : 'An error occurred while loading your tests.'}
          </Text>
          <Group>
            <Button onClick={() => refetch()} variant="outline">
              Try Again
            </Button>
            <Button onClick={() => navigate('/upload')}>
              Upload New Test
            </Button>
          </Group>
        </Alert>
      </Container>
    )
  }

  // Empty state (keep existing)
  if (tests.length === 0) {
    return (
      <Container size="md" py="xl">
        <Card shadow="sm" p="xl" withBorder>
          <Title order={2} mb="md">No tests yet</Title>
          <Text c="dimmed" mb="xl">
            Upload your first audiogram to get started
          </Text>
          <Button onClick={() => navigate('/upload')} size="lg">
            Upload Test
          </Button>
        </Card>
      </Container>
    )
  }

  // Success state (existing render)
  return (
    <Container size="xl" py="xl">
      {/* ... existing dashboard content */}
    </Container>
  )
}

// TestViewer.tsx - similar changes
export function TestViewer() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const {
    data: test,
    isLoading,
    isError,
    error
  } = useQuery({
    queryKey: ['test', id],
    queryFn: () => getTest(id!),
    enabled: !!id,
    retry: 2
  })

  if (isLoading) {
    return (
      <Container>
        <Center h={200}>
          <Loader size="lg" />
        </Center>
      </Container>
    )
  }

  if (isError) {
    return (
      <Container size="md" py="xl">
        <Alert color="red" title="Failed to Load Test">
          <Text mb="md">
            {error instanceof Error ? error.message : 'Unable to load test details.'}
          </Text>
          <Group>
            <Button onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </Button>
            <Button onClick={() => navigate('/tests')} variant="outline">
              View All Tests
            </Button>
          </Group>
        </Alert>
      </Container>
    )
  }

  if (!test) {
    return (
      <Container size="md" py="xl">
        <Alert color="yellow" title="Test Not Found">
          <Text mb="md">
            The test you're looking for doesn't exist or has been deleted.
          </Text>
          <Button onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </Button>
        </Alert>
      </Container>
    )
  }

  // Success state (existing render)
  return (
    <Container size="xl" py="xl">
      {/* ... existing test viewer content */}
    </Container>
  )
}
```

- **Pro:** Clear error messages
- **Pro:** Retry mechanism
- **Pro:** Navigation recovery options
- **Pro:** Better UX
- **Pro:** Automatic retries with backoff

---

### Issue 3: No Delete Error Handling (TestViewer)

**Severity:** 🔴 CRITICAL (High)
**Location:** `frontend/src/pages/TestViewer.tsx:20-26`
**Category:** Error Handling / Data Loss

**Description:**

Delete mutation has no `onError` handler. If delete fails, user thinks it succeeded (modal closes, navigated away) but test still exists.

**Current Code:**

```tsx
const deleteMutation = useMutation({
  mutationFn: () => deleteTest(id!),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['tests'] })
    navigate('/dashboard')
  }
  // Missing onError!
})
```

**Solution:**

```tsx
const deleteMutation = useMutation({
  mutationFn: () => deleteTest(id!),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['tests'] })
    notifications.show({
      title: 'Test Deleted',
      message: 'The test has been successfully deleted',
      color: 'green'
    })
    navigate('/dashboard')
  },
  onError: (error) => {
    notifications.show({
      title: 'Delete Failed',
      message: error instanceof Error ? error.message : 'Failed to delete test',
      color: 'red',
      autoClose: false
    })
    // Keep modal open so user can retry
  }
})

// Show error in modal
<Modal
  opened={deleteModalOpen}
  onClose={() => setDeleteModalOpen(false)}
  title="Delete Test"
>
  <Text mb="md">Are you sure you want to delete this test? This action cannot be undone.</Text>

  {deleteMutation.isError && (
    <Alert color="red" mb="md" title="Delete Failed">
      {deleteMutation.error instanceof Error ? deleteMutation.error.message : 'An error occurred'}
    </Alert>
  )}

  <Group justify="flex-end">
    <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
      Cancel
    </Button>
    <Button
      color="red"
      onClick={() => deleteMutation.mutate()}
      loading={deleteMutation.isPending}
    >
      Delete
    </Button>
  </Group>
</Modal>
```

---

## Configuration & Setup Issues

### Issue 4: No QueryClient Configuration

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/main.tsx:8`
**Category:** Performance / UX

**Description:**

QueryClient instantiated with default settings. No custom retry logic, cache time, or error handlers configured.

**Current Code:**

```tsx
const queryClient = new QueryClient()  // Defaults only
```

**Solution:**

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Retry configuration
      retry: (failureCount, error: any) => {
        // Don't retry on 404s
        if (error?.response?.status === 404) return false
        // Retry up to 3 times for other errors
        return failureCount < 3
      },
      retryDelay: (attemptIndex) =>
        Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff

      // Cache configuration
      staleTime: 60 * 1000, // 1 minute
      cacheTime: 5 * 60 * 1000, // 5 minutes

      // Refetch configuration
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      refetchOnMount: true,

      // Error handling
      onError: (error) => {
        console.error('Query error:', error)
        // Global error notification for network issues
        if (error instanceof Error && error.message.includes('Network')) {
          notifications.show({
            title: 'Network Error',
            message: 'Please check your internet connection',
            color: 'red'
          })
        }
      }
    },
    mutations: {
      // Mutation defaults
      retry: false, // Don't auto-retry mutations
      onError: (error) => {
        console.error('Mutation error:', error)
      }
    }
  }
})
```

---

### Issue 5: No 404 Catch-All Route

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/App.tsx:16-25`
**Category:** UX

**Description:**

Router has no wildcard route. Users navigating to invalid URLs see blank page.

**Solution:**

```tsx
// pages/NotFound.tsx
export function NotFound() {
  const navigate = useNavigate()

  return (
    <Container size="sm" py="xl">
      <Alert color="blue" title="Page Not Found">
        <Text mb="md">The page you're looking for doesn't exist.</Text>
        <Button onClick={() => navigate('/dashboard')}>
          Go to Dashboard
        </Button>
      </Alert>
    </Container>
  )
}

// App.tsx
<Routes>
  <Route path="/" element={<AppLayout />}>
    <Route index element={<Navigate to="/dashboard" replace />} />
    {/* ... other routes */}
    <Route path="*" element={<NotFound />} />  {/* Catch-all */}
  </Route>
</Routes>
```

---

## Data Validation & Edge Cases

### Issue 6: Unsafe Date Operations

**Severity:** 🟡 MEDIUM
**Location:**
- `frontend/src/pages/Dashboard.tsx:15, 42, 51, 65, 72, 101`
- `frontend/src/pages/TestViewer.tsx:42, 65`

**Category:** Data Validation / Reliability

**Description:**

`new Date(dateString)` called throughout without validation. Invalid dates result in Invalid Date objects, causing NaN in comparisons and incorrect rendering.

**Solution:**

```tsx
// lib/date-utils.ts
export function parseDate(dateString: string | undefined | null): Date | null {
  if (!dateString) return null

  const date = new Date(dateString)

  // Check if date is valid
  if (isNaN(date.getTime())) {
    console.warn('Invalid date string:', dateString)
    return null
  }

  return date
}

export function formatDate(dateString: string | undefined | null): string {
  const date = parseDate(dateString)
  return date ? date.toLocaleDateString() : '-'
}

// Dashboard.tsx
import { parseDate, formatDate } from '../lib/date-utils'

const testsThisYear = tests.filter(t => {
  const date = parseDate(t.test_date)
  return date && date.getFullYear() === new Date().getFullYear()
}).length

// ...

<Text size="xl" fw={700}>
  {formatDate(latestTest?.test_date)}
</Text>
```

---

## Summary & Recommendations

### Critical Priority (Implement Immediately)

1. **Add Error Boundaries** (Issue 1)
   - Root-level and feature-level boundaries
   - Graceful error recovery
   - User-friendly error messages

2. **Add Error State Handling** (Issue 2)
   - Handle isError in all useQuery calls
   - Show error messages with retry
   - Automatic retry with backoff

3. **Add Delete Error Handling** (Issue 3)
   - onError handler for mutations
   - Keep modal open on failure
   - Clear error messages

### High Priority (Important)

4. **Configure QueryClient** (Issue 4)
   - Retry logic with exponential backoff
   - Cache configuration
   - Global error handlers

5. **Add 404 Route** (Issue 5)
   - Catch-all route
   - Helpful error page
   - Navigation back to app

### Medium Priority (Nice to Have)

6. **Safe Date Handling** (Issue 6)
   - Validation utility
   - Consistent formatting
   - Handle invalid dates gracefully

### Code Changes Summary

**New Files:**
- `frontend/src/components/ErrorBoundary.tsx`
- `frontend/src/pages/NotFound.tsx`
- `frontend/src/lib/date-utils.ts`

**Modified Files:**
- `frontend/src/App.tsx` - Add ErrorBoundary, 404 route
- `frontend/src/main.tsx` - Configure QueryClient
- `frontend/src/pages/Dashboard.tsx` - Error handling, date utils
- `frontend/src/pages/TestViewer.tsx` - Error handling, date utils

**Estimated Effort:** 4-6 hours for all critical + high priority issues
