# Navigation and UI Structure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build complete app navigation with dashboard, test list, test viewer, and review/edit pages.

**Architecture:** React Router for navigation, Mantine AppShell for layout, Recharts for audiogram visualization. Confidence-based routing (≥80% direct to viewer, <80% to review page).

**Tech Stack:** React Router v6, Recharts, Mantine UI, TanStack React Query, Axios

---

## Phase 1: Install Dependencies and Setup Router

### Task 1: Install Required Dependencies

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install dependencies**

```bash
cd frontend
npm install react-router-dom recharts
npm install --save-dev @types/react-router-dom
```

Expected: Dependencies installed successfully

**Step 2: Verify installation**

```bash
npm list react-router-dom recharts
```

Expected: Shows installed versions

**Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "deps: add react-router-dom and recharts for navigation and charts"
```

---

### Task 2: Create Directory Structure

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/TestList.tsx`
- Create: `frontend/src/pages/TestViewer.tsx`
- Create: `frontend/src/pages/TestReviewEdit.tsx`
- Create: `frontend/src/components/AppLayout.tsx`
- Create: `frontend/src/components/Navigation.tsx`

**Step 1: Create placeholder pages**

Create `frontend/src/pages/Dashboard.tsx`:
```tsx
export function Dashboard() {
  return <div>Dashboard Page</div>
}
```

Create `frontend/src/pages/TestList.tsx`:
```tsx
export function TestList() {
  return <div>Test List Page</div>
}
```

Create `frontend/src/pages/TestViewer.tsx`:
```tsx
export function TestViewer() {
  return <div>Test Viewer Page</div>
}
```

Create `frontend/src/pages/TestReviewEdit.tsx`:
```tsx
export function TestReviewEdit() {
  return <div>Test Review/Edit Page</div>
}
```

**Step 2: Verify files created**

```bash
ls frontend/src/pages/
```

Expected: Shows all 4 .tsx files

**Step 3: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: create placeholder page components"
```

---

### Task 3: Create Navigation Component

**Files:**
- Create: `frontend/src/components/Navigation.tsx`

**Step 1: Create Navigation component**

```tsx
import { NavLink } from 'react-router-dom'
import { Group, Title } from '@mantine/core'
import classes from './Navigation.module.css'

export function Navigation() {
  return (
    <Group h="100%" px="md" justify="space-between">
      <Title order={3}>Hearing Test Tracker</Title>

      <Group gap="xl">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => isActive ? classes.linkActive : classes.link}
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/upload"
          className={({ isActive }) => isActive ? classes.linkActive : classes.link}
        >
          Upload Test
        </NavLink>
        <NavLink
          to="/tests"
          className={({ isActive }) => isActive ? classes.linkActive : classes.link}
        >
          All Tests
        </NavLink>
      </Group>
    </Group>
  )
}
```

**Step 2: Create Navigation styles**

Create `frontend/src/components/Navigation.module.css`:
```css
.link {
  text-decoration: none;
  color: var(--mantine-color-gray-7);
  font-weight: 500;
  transition: color 0.2s;
}

.link:hover {
  color: var(--mantine-color-blue-6);
}

.linkActive {
  text-decoration: none;
  color: var(--mantine-color-blue-6);
  font-weight: 600;
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/Navigation.tsx frontend/src/components/Navigation.module.css
git commit -m "feat: add navigation component with links"
```

---

### Task 4: Create AppLayout with AppShell

**Files:**
- Create: `frontend/src/components/AppLayout.tsx`

**Step 1: Create AppLayout component**

```tsx
import { AppShell } from '@mantine/core'
import { Outlet } from 'react-router-dom'
import { Navigation } from './Navigation'

export function AppLayout() {
  return (
    <AppShell
      header={{ height: 60 }}
      padding="md"
    >
      <AppShell.Header>
        <Navigation />
      </AppShell.Header>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/AppLayout.tsx
git commit -m "feat: add AppLayout with Mantine AppShell"
```

---

### Task 5: Add Router to App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Read current App.tsx**

Expected: Currently shows Container with UploadForm

**Step 2: Replace with router setup**

```tsx
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
```

**Step 3: Test in browser**

```bash
# Ensure frontend dev server is running
npm run dev
```

Navigate to http://localhost:3000
Expected: See navigation bar, "Dashboard Page" text, can click links

**Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add React Router with all routes"
```

---

## Phase 2: Backend API Extensions

### Task 6: Add Update Test Endpoint

**Files:**
- Modify: `backend/api/routes.py`

**Step 1: Add update endpoint after get_test function**

```python
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """
    Update test data after manual review.

    Request:
        {
            'test_date': str,
            'location': str,
            'device_name': str,
            'notes': str,
            'left_ear': [{'frequency_hz': int, 'threshold_db': float}, ...],
            'right_ear': [{'frequency_hz': int, 'threshold_db': float}, ...]
        }

    Response:
        Updated test object (same as GET /tests/:id)
    """
    data = request.json
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Verify test exists
    cursor.execute("SELECT id FROM hearing_test WHERE id = ?", (test_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Test not found'}), 404

    # Update test metadata
    cursor.execute("""
        UPDATE hearing_test
        SET test_date = ?,
            location = ?,
            device_name = ?,
            notes = ?
        WHERE id = ?
    """, (
        data['test_date'],
        data.get('location'),
        data.get('device_name'),
        data.get('notes'),
        test_id
    ))

    # Delete existing measurements
    cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test_id,))

    # Insert new measurements (deduplicated)
    for ear_name, ear_data in [('left', data['left_ear']), ('right', data['right_ear'])]:
        deduplicated = _deduplicate_measurements(ear_data)
        for measurement in deduplicated:
            cursor.execute("""
                INSERT INTO audiogram_measurement (
                    id, id_hearing_test, ear, frequency_hz, threshold_db
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                generate_uuid(),
                test_id,
                ear_name,
                measurement['frequency_hz'],
                measurement['threshold_db']
            ))

    conn.commit()
    conn.close()

    # Return updated test
    return get_test(test_id)
```

**Step 2: Test with curl**

```bash
# First get a test ID
curl http://localhost:5001/api/tests

# Then update it
curl -X PUT http://localhost:5001/api/tests/{test_id} \
  -H "Content-Type: application/json" \
  -d '{
    "test_date": "2025-01-15",
    "location": "Home",
    "device_name": "Jacoti",
    "notes": "Updated notes",
    "left_ear": [{"frequency_hz": 125, "threshold_db": 25}],
    "right_ear": [{"frequency_hz": 125, "threshold_db": 30}]
  }'
```

Expected: Returns updated test object

**Step 3: Commit**

```bash
git add backend/api/routes.py
git commit -m "feat: add PUT /api/tests/:id endpoint for updating tests"
```

---

### Task 7: Add Delete Test Endpoint

**Files:**
- Modify: `backend/api/routes.py`

**Step 1: Add delete endpoint after update_test**

```python
@api_bp.route('/tests/<test_id>', methods=['DELETE'])
def delete_test(test_id):
    """
    Delete a test and its measurements.

    Response:
        {'success': true}
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Verify test exists
    cursor.execute("SELECT id, image_path FROM hearing_test WHERE id = ?", (test_id,))
    test = cursor.fetchone()

    if not test:
        conn.close()
        return jsonify({'error': 'Test not found'}), 404

    # Delete measurements (cascade should handle this, but explicit is clear)
    cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test_id,))

    # Delete test
    cursor.execute("DELETE FROM hearing_test WHERE id = ?", (test_id,))

    conn.commit()
    conn.close()

    # Delete image file if it exists
    if test['image_path']:
        image_path = Path(test['image_path'])
        if image_path.exists():
            image_path.unlink()

    return jsonify({'success': True})
```

**Step 2: Add Path import at top of file**

Add to imports:
```python
from pathlib import Path
```

**Step 3: Test with curl**

```bash
# Delete a test
curl -X DELETE http://localhost:5001/api/tests/{test_id}
```

Expected: Returns {"success": true}

**Step 4: Commit**

```bash
git add backend/api/routes.py
git commit -m "feat: add DELETE /api/tests/:id endpoint"
```

---

### Task 8: Add API Functions to Frontend

**Files:**
- Modify: `frontend/src/lib/api.ts`

**Step 1: Add update and delete functions**

Add after existing functions:
```typescript
export const updateTest = async (testId: string, data: {
  test_date: string
  location?: string
  device_name?: string
  notes?: string
  left_ear: AudiogramMeasurement[]
  right_ear: AudiogramMeasurement[]
}): Promise<UploadResponse> => {
  const response = await apiClient.put<UploadResponse>(`/tests/${testId}`, data)
  return response.data
}

export const deleteTest = async (testId: string): Promise<void> => {
  await apiClient.delete(`/tests/${testId}`)
}

export interface TestDetail {
  id: string
  test_date: string
  source_type: string
  location: string
  left_ear: AudiogramMeasurement[]
  right_ear: AudiogramMeasurement[]
  metadata: {
    device: string
    technician: string
    notes: string
  }
}

export const getTest = async (testId: string): Promise<TestDetail> => {
  const response = await apiClient.get<TestDetail>(`/tests/${testId}`)
  return response.data
}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: add update, delete, and getTest API functions"
```

---

## Phase 3: Dashboard Implementation

### Task 9: Implement Dashboard Component

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`

**Step 1: Replace Dashboard placeholder**

```tsx
import { Container, Grid, Card, Text, Table, Button, Badge, Group, Title } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { listTests, type HearingTest } from '../lib/api'

export function Dashboard() {
  const navigate = useNavigate()
  const { data: tests = [], isLoading } = useQuery({
    queryKey: ['tests'],
    queryFn: listTests
  })

  const latestTest = tests[0]
  const testsThisYear = tests.filter(t =>
    new Date(t.test_date).getFullYear() === new Date().getFullYear()
  ).length

  if (isLoading) {
    return <Container><Text>Loading...</Text></Container>
  }

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

  return (
    <Container size="xl" py="xl">
      <Grid>
        <Grid.Col span={4}>
          <Card shadow="sm" p="md" withBorder>
            <Text size="sm" c="dimmed">Total Tests</Text>
            <Text size="xl" fw={700}>{tests.length}</Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={4}>
          <Card shadow="sm" p="md" withBorder>
            <Text size="sm" c="dimmed">Latest Test</Text>
            <Text size="xl" fw={700}>
              {latestTest ? new Date(latestTest.test_date).toLocaleDateString() : '-'}
            </Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={4}>
          <Card shadow="sm" p="md" withBorder>
            <Text size="sm" c="dimmed">Tests This Year</Text>
            <Text size="xl" fw={700}>{testsThisYear}</Text>
          </Card>
        </Grid.Col>
      </Grid>

      {latestTest && (
        <Card shadow="sm" p="md" withBorder mt="xl">
          <Group justify="space-between" mb="md">
            <Title order={3}>Latest Test</Title>
            <Badge color={latestTest.confidence >= 0.8 ? 'green' : 'yellow'}>
              {(latestTest.confidence * 100).toFixed(0)}% confidence
            </Badge>
          </Group>
          <Text size="sm" c="dimmed" mb="xs">
            {new Date(latestTest.test_date).toLocaleDateString()} • {latestTest.location}
          </Text>
          <Button onClick={() => navigate(`/tests/${latestTest.id}`)} mt="md">
            View Details
          </Button>
        </Card>
      )}

      <Card shadow="sm" p="md" withBorder mt="xl">
        <Group justify="space-between" mb="md">
          <Title order={3}>Recent Tests</Title>
          <Button variant="subtle" onClick={() => navigate('/tests')}>
            View All
          </Button>
        </Group>

        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Date</Table.Th>
              <Table.Th>Location</Table.Th>
              <Table.Th>Source</Table.Th>
              <Table.Th>Confidence</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {tests.slice(0, 10).map((test) => (
              <Table.Tr key={test.id}>
                <Table.Td>{new Date(test.test_date).toLocaleDateString()}</Table.Td>
                <Table.Td>{test.location}</Table.Td>
                <Table.Td>{test.source_type}</Table.Td>
                <Table.Td>
                  <Badge color={test.confidence >= 0.8 ? 'green' : 'yellow'} size="sm">
                    {(test.confidence * 100).toFixed(0)}%
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Button size="xs" variant="light" onClick={() => navigate(`/tests/${test.id}`)}>
                    View
                  </Button>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Card>
    </Container>
  )
}
```

**Step 2: Test in browser**

Navigate to http://localhost:3000/dashboard
Expected: Shows stats cards, latest test card, recent tests table

**Step 3: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx
git commit -m "feat: implement dashboard with stats and recent tests"
```

---

## Phase 4: Test List Implementation

### Task 10: Implement TestList Component

**Files:**
- Modify: `frontend/src/pages/TestList.tsx`

**Step 1: Replace TestList placeholder**

```tsx
import { Container, Title, Table, Button, Badge, Group } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { listTests } from '../lib/api'

export function TestList() {
  const navigate = useNavigate()
  const { data: tests = [], isLoading } = useQuery({
    queryKey: ['tests'],
    queryFn: listTests
  })

  if (isLoading) {
    return <Container><Title>Loading...</Title></Container>
  }

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>All Tests</Title>
          <Title order={4} c="dimmed" fw={400}>
            Showing {tests.length} test{tests.length !== 1 ? 's' : ''}
          </Title>
        </div>
        <Button onClick={() => navigate('/upload')}>
          Upload New Test
        </Button>
      </Group>

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Date</Table.Th>
            <Table.Th>Location</Table.Th>
            <Table.Th>Source</Table.Th>
            <Table.Th>Device</Table.Th>
            <Table.Th>Confidence</Table.Th>
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {tests.map((test) => (
            <Table.Tr
              key={test.id}
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/tests/${test.id}`)}
            >
              <Table.Td>{new Date(test.test_date).toLocaleDateString()}</Table.Td>
              <Table.Td>{test.location}</Table.Td>
              <Table.Td>{test.source_type}</Table.Td>
              <Table.Td>{test.id}</Table.Td>
              <Table.Td>
                <Badge color={test.confidence >= 0.8 ? 'green' : 'yellow'}>
                  {(test.confidence * 100).toFixed(0)}%
                </Badge>
              </Table.Td>
              <Table.Td onClick={(e) => e.stopPropagation()}>
                <Button
                  size="xs"
                  variant="light"
                  onClick={() => navigate(`/tests/${test.id}`)}
                >
                  View
                </Button>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Container>
  )
}
```

**Step 2: Test in browser**

Navigate to http://localhost:3000/tests
Expected: Shows table with all tests, clicking row navigates to test viewer

**Step 3: Commit**

```bash
git add frontend/src/pages/TestList.tsx
git commit -m "feat: implement test list with sortable table"
```

---

## Phase 5: Test Viewer with Audiogram Chart

### Task 11: Create AudiogramChart Component

**Files:**
- Create: `frontend/src/components/AudiogramChart.tsx`

**Step 1: Create AudiogramChart component**

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceArea } from 'recharts'
import { type AudiogramMeasurement } from '../lib/api'

interface AudiogramChartProps {
  leftEar: AudiogramMeasurement[]
  rightEar: AudiogramMeasurement[]
}

export function AudiogramChart({ leftEar, rightEar }: AudiogramChartProps) {
  // Combine data by frequency
  const frequencies = [125, 250, 500, 1000, 2000, 4000, 8000]
  const chartData = frequencies.map(freq => {
    const leftPoint = leftEar.find(m => m.frequency_hz === freq)
    const rightPoint = rightEar.find(m => m.frequency_hz === freq)

    return {
      frequency: freq,
      left: leftPoint?.threshold_db,
      right: rightPoint?.threshold_db
    }
  })

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />

        {/* Background zones */}
        <ReferenceArea y1={0} y2={25} fill="green" fillOpacity={0.1} />
        <ReferenceArea y1={25} y2={40} fill="yellow" fillOpacity={0.1} />
        <ReferenceArea y1={40} y2={55} fill="orange" fillOpacity={0.1} />
        <ReferenceArea y1={55} y2={120} fill="red" fillOpacity={0.1} />

        <XAxis
          dataKey="frequency"
          label={{ value: 'Frequency (Hz)', position: 'bottom' }}
          scale="log"
          domain={[125, 8000]}
          ticks={frequencies}
        />
        <YAxis
          label={{ value: 'Hearing Loss (dB HL)', angle: -90, position: 'insideLeft' }}
          reversed
          domain={[0, 120]}
        />
        <Tooltip />
        <Legend />

        <Line
          type="monotone"
          dataKey="right"
          stroke="#ff0000"
          strokeWidth={2}
          name="Right Ear"
          dot={{ fill: '#ff0000', r: 5 }}
        />
        <Line
          type="monotone"
          dataKey="left"
          stroke="#0000ff"
          strokeWidth={2}
          name="Left Ear"
          dot={{ fill: '#0000ff', r: 5, symbol: 'cross' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/AudiogramChart.tsx
git commit -m "feat: add audiogram chart component with Recharts"
```

---

### Task 12: Implement TestViewer Component

**Files:**
- Modify: `frontend/src/pages/TestViewer.tsx`

**Step 1: Replace TestViewer placeholder**

```tsx
import { Container, Title, Text, Group, Badge, Button, Card, Grid, Table, Tabs, Modal } from '@mantine/core'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { getTest, deleteTest } from '../lib/api'
import { AudiogramChart } from '../components/AudiogramChart'

export function TestViewer() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)

  const { data: test, isLoading } = useQuery({
    queryKey: ['test', id],
    queryFn: () => getTest(id!),
    enabled: !!id
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteTest(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      navigate('/dashboard')
    }
  })

  if (isLoading) {
    return <Container><Text>Loading...</Text></Container>
  }

  if (!test) {
    return <Container><Text>Test not found</Text></Container>
  }

  const confidence = test.metadata?.confidence || 0

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>{new Date(test.test_date).toLocaleDateString()}</Title>
          <Text c="dimmed" size="lg">
            {test.location} • {test.source_type}
          </Text>
        </div>
        <Group>
          <Badge color={confidence >= 0.8 ? 'green' : 'yellow'} size="lg">
            {(confidence * 100).toFixed(0)}% confidence
          </Badge>
          <Button onClick={() => navigate(`/tests/${id}/review`)}>
            Edit Test Data
          </Button>
          <Button color="red" variant="outline" onClick={() => setDeleteModalOpen(true)}>
            Delete Test
          </Button>
        </Group>
      </Group>

      <Card shadow="sm" p="md" withBorder mb="xl">
        <Title order={3} mb="md">Test Information</Title>
        <Grid>
          <Grid.Col span={6}>
            <Text size="sm" c="dimmed">Test Date</Text>
            <Text>{new Date(test.test_date).toLocaleDateString()}</Text>
          </Grid.Col>
          <Grid.Col span={6}>
            <Text size="sm" c="dimmed">Location</Text>
            <Text>{test.location}</Text>
          </Grid.Col>
          <Grid.Col span={6}>
            <Text size="sm" c="dimmed">Source Type</Text>
            <Text>{test.source_type}</Text>
          </Grid.Col>
          <Grid.Col span={6}>
            <Text size="sm" c="dimmed">Device</Text>
            <Text>{test.metadata?.device || '-'}</Text>
          </Grid.Col>
          {test.metadata?.notes && (
            <Grid.Col span={12}>
              <Text size="sm" c="dimmed">Notes</Text>
              <Text>{test.metadata.notes}</Text>
            </Grid.Col>
          )}
        </Grid>
      </Card>

      <Card shadow="sm" p="md" withBorder mb="xl">
        <Title order={3} mb="md">Audiogram</Title>
        <AudiogramChart leftEar={test.left_ear} rightEar={test.right_ear} />
      </Card>

      <Card shadow="sm" p="md" withBorder>
        <Title order={3} mb="md">Measurements</Title>
        <Tabs defaultValue="left">
          <Tabs.List>
            <Tabs.Tab value="left">Left Ear</Tabs.Tab>
            <Tabs.Tab value="right">Right Ear</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="left" pt="md">
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Frequency (Hz)</Table.Th>
                  <Table.Th>Threshold (dB)</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {test.left_ear.map((m) => (
                  <Table.Tr key={m.frequency_hz}>
                    <Table.Td>{m.frequency_hz}</Table.Td>
                    <Table.Td>{m.threshold_db.toFixed(1)}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Tabs.Panel>

          <Tabs.Panel value="right" pt="md">
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Frequency (Hz)</Table.Th>
                  <Table.Th>Threshold (dB)</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {test.right_ear.map((m) => (
                  <Table.Tr key={m.frequency_hz}>
                    <Table.Td>{m.frequency_hz}</Table.Td>
                    <Table.Td>{m.threshold_db.toFixed(1)}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Tabs.Panel>
        </Tabs>
      </Card>

      <Modal
        opened={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Test"
      >
        <Text mb="md">Are you sure you want to delete this test? This action cannot be undone.</Text>
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
    </Container>
  )
}
```

**Step 2: Test in browser**

Navigate to http://localhost:3000/tests/{id}
Expected: Shows test details, audiogram chart, measurement tables

**Step 3: Commit**

```bash
git add frontend/src/pages/TestViewer.tsx
git commit -m "feat: implement test viewer with chart and metadata"
```

---

## Phase 6: Review/Edit Page

### Task 13: Implement TestReviewEdit Component

**Files:**
- Modify: `frontend/src/pages/TestReviewEdit.tsx`

**Step 1: Replace TestReviewEdit placeholder**

```tsx
import { Container, Title, Grid, Image, Card, TextInput, Textarea, Tabs, Table, NumberInput, Group, Button, Badge } from '@mantine/core'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getTest, updateTest, type AudiogramMeasurement } from '../lib/api'
import { DateInput } from '@mantine/dates'

export function TestReviewEdit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: test, isLoading } = useQuery({
    queryKey: ['test', id],
    queryFn: () => getTest(id!),
    enabled: !!id
  })

  const [testDate, setTestDate] = useState<Date | null>(null)
  const [location, setLocation] = useState('')
  const [device, setDevice] = useState('')
  const [notes, setNotes] = useState('')
  const [leftEar, setLeftEar] = useState<AudiogramMeasurement[]>([])
  const [rightEar, setRightEar] = useState<AudiogramMeasurement[]>([])

  useEffect(() => {
    if (test) {
      setTestDate(new Date(test.test_date))
      setLocation(test.location || '')
      setDevice(test.metadata?.device || '')
      setNotes(test.metadata?.notes || '')
      setLeftEar(test.left_ear)
      setRightEar(test.right_ear)
    }
  }, [test])

  const updateMutation = useMutation({
    mutationFn: () => updateTest(id!, {
      test_date: testDate!.toISOString().split('T')[0],
      location,
      device_name: device,
      notes,
      left_ear: leftEar,
      right_ear: rightEar
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test', id] })
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      navigate(`/tests/${id}`)
    }
  })

  const updateLeftEar = (index: number, value: number) => {
    const updated = [...leftEar]
    updated[index] = { ...updated[index], threshold_db: value }
    setLeftEar(updated)
  }

  const updateRightEar = (index: number, value: number) => {
    const updated = [...rightEar]
    updated[index] = { ...updated[index], threshold_db: value }
    setRightEar(updated)
  }

  if (isLoading) {
    return <Container><Title>Loading...</Title></Container>
  }

  if (!test) {
    return <Container><Title>Test not found</Title></Container>
  }

  const confidence = test.metadata?.confidence || 0
  const imagePath = test.metadata?.image_path

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>Review & Edit Test</Title>
          <Badge color={confidence >= 0.8 ? 'green' : 'yellow'} size="lg" mt="xs">
            {(confidence * 100).toFixed(0)}% confidence
          </Badge>
        </div>
      </Group>

      <Grid>
        <Grid.Col span={7}>
          {imagePath && (
            <Card shadow="sm" p="md" withBorder>
              <Title order={4} mb="md">Original Image</Title>
              <Image
                src={`/api/images/${imagePath}`}
                alt="Original audiogram"
                fit="contain"
                style={{ cursor: 'zoom-in' }}
              />
            </Card>
          )}
        </Grid.Col>

        <Grid.Col span={5}>
          <Card shadow="sm" p="md" withBorder mb="md">
            <Title order={4} mb="md">Test Metadata</Title>
            <DateInput
              label="Test Date"
              value={testDate}
              onChange={setTestDate}
              mb="md"
            />
            <TextInput
              label="Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              mb="md"
            />
            <TextInput
              label="Device"
              value={device}
              onChange={(e) => setDevice(e.target.value)}
              mb="md"
            />
            <Textarea
              label="Notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              minRows={3}
            />
          </Card>

          <Card shadow="sm" p="md" withBorder>
            <Title order={4} mb="md">Audiogram Data</Title>
            <Tabs defaultValue="left">
              <Tabs.List>
                <Tabs.Tab value="left">Left Ear</Tabs.Tab>
                <Tabs.Tab value="right">Right Ear</Tabs.Tab>
              </Tabs.List>

              <Tabs.Panel value="left" pt="md">
                <Table>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Frequency (Hz)</Table.Th>
                      <Table.Th>Threshold (dB)</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {leftEar.map((m, idx) => (
                      <Table.Tr key={m.frequency_hz}>
                        <Table.Td>{m.frequency_hz}</Table.Td>
                        <Table.Td>
                          <NumberInput
                            value={m.threshold_db}
                            onChange={(val) => updateLeftEar(idx, val as number)}
                            min={0}
                            max={120}
                            step={5}
                            size="xs"
                          />
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </Tabs.Panel>

              <Tabs.Panel value="right" pt="md">
                <Table>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Frequency (Hz)</Table.Th>
                      <Table.Th>Threshold (dB)</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {rightEar.map((m, idx) => (
                      <Table.Tr key={m.frequency_hz}>
                        <Table.Td>{m.frequency_hz}</Table.Td>
                        <Table.Td>
                          <NumberInput
                            value={m.threshold_db}
                            onChange={(val) => updateRightEar(idx, val as number)}
                            min={0}
                            max={120}
                            step={5}
                            size="xs"
                          />
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </Tabs.Panel>
            </Tabs>
          </Card>

          <Group justify="flex-end" mt="xl">
            <Button variant="outline" onClick={() => navigate(`/tests/${id}`)}>
              Cancel
            </Button>
            <Button
              onClick={() => updateMutation.mutate()}
              loading={updateMutation.isPending}
            >
              Accept & Save
            </Button>
          </Group>
        </Grid.Col>
      </Grid>
    </Container>
  )
}
```

**Step 2: Install @mantine/dates**

```bash
cd frontend
npm install @mantine/dates dayjs
```

**Step 3: Test in browser**

Navigate to http://localhost:3000/tests/{id}/review
Expected: Shows image on left, editable form on right

**Step 4: Commit**

```bash
git add frontend/src/pages/TestReviewEdit.tsx frontend/package.json frontend/package-lock.json
git commit -m "feat: implement test review/edit page with image and form"
```

---

## Phase 7: Upload Integration

### Task 14: Update UploadForm to Navigate After Upload

**Files:**
- Modify: `frontend/src/components/UploadForm.tsx`

**Step 1: Add navigation after upload**

Replace the `uploadMutation` onSuccess handler:
```tsx
import { useNavigate } from 'react-router-dom'
import { notifications } from '@mantine/notifications'

export function UploadForm() {
  const navigate = useNavigate()
  // ... existing state

  const uploadMutation = useMutation({
    mutationFn: uploadAudiogram,
    onSuccess: (data) => {
      if (data.confidence >= 0.8) {
        notifications.show({
          title: 'Upload Successful',
          message: `Test uploaded with ${(data.confidence * 100).toFixed(0)}% confidence`,
          color: 'green'
        })
        navigate(`/tests/${data.test_id}`)
      } else {
        navigate(`/tests/${data.test_id}/review`)
      }
      queryClient.invalidateQueries({ queryKey: ['tests'] })
    }
  })

  // Remove all the inline result display code (result state, isEditing, etc.)
  // Keep only the file input and upload button
```

**Step 2: Install @mantine/notifications**

```bash
cd frontend
npm install @mantine/notifications
```

**Step 3: Add Notifications provider to App.tsx**

Add to imports:
```tsx
import { Notifications } from '@mantine/notifications'
import '@mantine/notifications/styles.css'
```

Wrap BrowserRouter:
```tsx
<>
  <Notifications />
  <BrowserRouter>
    {/* existing routes */}
  </BrowserRouter>
</>
```

**Step 4: Simplify UploadForm return**

```tsx
return (
  <Stack>
    <FileInput
      label="Upload Audiogram"
      placeholder="Select JPEG image"
      accept="image/jpeg,image/jpg"
      value={file}
      onChange={setFile}
    />

    <Button
      onClick={handleUpload}
      disabled={!file || uploadMutation.isPending}
      loading={uploadMutation.isPending}
    >
      Process Audiogram
    </Button>

    {uploadMutation.isError && (
      <Alert color="red" title="Upload Failed">
        {uploadMutation.error.message}
      </Alert>
    )}
  </Stack>
)
```

**Step 5: Test upload flow**

1. Go to /upload
2. Upload a test
3. If confidence >= 80%: Should navigate to test viewer
4. If confidence < 80%: Should navigate to review page

**Step 6: Commit**

```bash
git add frontend/src/components/UploadForm.tsx frontend/src/App.tsx frontend/package.json frontend/package-lock.json
git commit -m "feat: update upload to navigate based on confidence"
```

---

## Phase 8: Polish & Testing

### Task 15: Wrap UploadForm in Container

**Files:**
- Create: `frontend/src/pages/Upload.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create Upload page wrapper**

```tsx
import { Container, Title, Paper } from '@mantine/core'
import { UploadForm } from '../components/UploadForm'

export function Upload() {
  return (
    <Container size="md" py="xl">
      <Title order={1} mb="xl">Upload Hearing Test</Title>
      <Paper shadow="sm" p="md" withBorder>
        <UploadForm />
      </Paper>
    </Container>
  )
}
```

**Step 2: Update App.tsx route**

Change upload route:
```tsx
import { Upload } from './pages/Upload'

// In routes:
<Route path="upload" element={<Upload />} />
```

**Step 3: Commit**

```bash
git add frontend/src/pages/Upload.tsx frontend/src/App.tsx
git commit -m "feat: wrap upload form in container page"
```

---

### Task 16: Add Loading States

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Modify: `frontend/src/pages/TestList.tsx`
- Modify: `frontend/src/pages/TestViewer.tsx`
- Modify: `frontend/src/pages/TestReviewEdit.tsx`

**Step 1: Add Skeleton loading to Dashboard**

Replace loading check:
```tsx
import { Skeleton } from '@mantine/core'

if (isLoading) {
  return (
    <Container size="xl" py="xl">
      <Grid>
        <Grid.Col span={4}><Skeleton height={100} /></Grid.Col>
        <Grid.Col span={4}><Skeleton height={100} /></Grid.Col>
        <Grid.Col span={4}><Skeleton height={100} /></Grid.Col>
      </Grid>
      <Skeleton height={200} mt="xl" />
      <Skeleton height={400} mt="xl" />
    </Container>
  )
}
```

**Step 2: Add loading to TestList, TestViewer, TestReviewEdit**

Similar skeleton pattern for each page

**Step 3: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: add skeleton loading states to all pages"
```

---

### Task 17: Add Error Boundaries

**Files:**
- Create: `frontend/src/components/ErrorBoundary.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create ErrorBoundary component**

```tsx
import { Component, ReactNode } from 'react'
import { Container, Title, Text, Button } from '@mantine/core'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <Container py="xl">
          <Title order={1} mb="md">Something went wrong</Title>
          <Text mb="md">An error occurred while loading this page.</Text>
          <Button onClick={() => window.location.reload()}>
            Reload Page
          </Button>
        </Container>
      )
    }

    return this.props.children
  }
}
```

**Step 2: Wrap App in ErrorBoundary**

In main.tsx or App.tsx:
```tsx
<ErrorBoundary>
  <BrowserRouter>
    {/* routes */}
  </BrowserRouter>
</ErrorBoundary>
```

**Step 3: Commit**

```bash
git add frontend/src/components/ErrorBoundary.tsx
git commit -m "feat: add error boundary for graceful error handling"
```

---

### Task 18: Final Testing Checklist

**Step 1: Test all navigation flows**

- [ ] Navigate between all pages via navbar
- [ ] Dashboard → Test viewer works
- [ ] Test list → Test viewer works
- [ ] Upload → Test viewer (high confidence) works
- [ ] Upload → Review page (low confidence) works
- [ ] Review page → Test viewer works

**Step 2: Test CRUD operations**

- [ ] Create: Upload new test
- [ ] Read: View test details
- [ ] Update: Edit test data and save
- [ ] Delete: Delete test with confirmation

**Step 3: Test edge cases**

- [ ] No tests (empty state shows)
- [ ] Loading states display correctly
- [ ] Error states display correctly
- [ ] Network errors are handled

**Step 4: Test responsive design**

- [ ] Works on desktop
- [ ] Works on tablet (if applicable)
- [ ] Navigation collapses properly

**Step 5: Create final commit**

```bash
git add -A
git commit -m "chore: final polish and testing"
```

---

## Summary

This plan implements:
- ✅ Complete navigation structure with React Router
- ✅ Dashboard with stats and recent tests
- ✅ Test list with sortable table
- ✅ Test viewer with audiogram chart
- ✅ Review/edit page with side-by-side layout
- ✅ Backend API extensions (PUT, DELETE)
- ✅ Confidence-based upload routing
- ✅ Loading states and error handling

**Total estimated time:** 4-6 hours
**Total commits:** ~18
