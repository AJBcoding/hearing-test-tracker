import { Tabs, Select, Stack, Loader, Text, Alert } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import { listTests, getTest } from '../lib/api'
import { AudiogramChart } from './AudiogramChart'
import { FrequencyTrendChart } from './FrequencyTrendChart'
import { TestCalendarHeatmap } from './TestCalendarHeatmap'
import { AudiogramAnimation } from './AudiogramAnimation'
import { ComparisonGrid } from './ComparisonGrid'

export function AudiogramViewer() {
  const [selectedTestId, setSelectedTestId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<string>('audiogram')

  // Fetch all tests
  const { data: tests, isLoading: testsLoading, error: testsError } = useQuery({
    queryKey: ['tests'],
    queryFn: listTests
  })

  // Fetch selected test details
  const { data: selectedTest, isLoading: testLoading } = useQuery({
    queryKey: ['test', selectedTestId],
    queryFn: () => getTest(selectedTestId!),
    enabled: !!selectedTestId && activeTab === 'audiogram'
  })

  // Fetch all test details for modes that need them
  const testIds = tests?.map(t => t.id) ?? []
  const { data: allTestDetails } = useQuery({
    queryKey: ['all-tests', testIds],
    queryFn: async () => {
      if (testIds.length === 0) return []
      const promises = testIds.map(id => getTest(id))
      return Promise.all(promises)
    },
    enabled: testIds.length > 0 && ['animation', 'compare'].includes(activeTab)
  })

  // Auto-select most recent test
  useMemo(() => {
    if (tests && tests.length > 0 && !selectedTestId) {
      setSelectedTestId(tests[0].id)
    }
  }, [tests, selectedTestId])

  // Helper function for trend chart
  const getTestMeasurements = (_testId: string) => {
    // This is a simplified version - in production, we'd fetch the actual measurements
    // For now, return null to indicate we need to fetch the data
    return { left: null, right: null }
  }

  if (testsLoading) {
    return (
      <Stack align="center" justify="center" py="xl">
        <Loader size="lg" />
        <Text size="sm" c="dimmed">Loading tests...</Text>
      </Stack>
    )
  }

  if (testsError) {
    return (
      <Alert color="red" title="Error loading tests">
        {testsError instanceof Error ? testsError.message : 'Failed to load tests'}
      </Alert>
    )
  }

  if (!tests || tests.length === 0) {
    return (
      <Alert color="blue" title="No tests available">
        Upload your first audiogram to get started with visualization.
      </Alert>
    )
  }

  return (
    <Stack gap="md">
      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'audiogram')}>
        <Tabs.List>
          <Tabs.Tab value="audiogram">Audiogram</Tabs.Tab>
          <Tabs.Tab value="trends">Trends</Tabs.Tab>
          <Tabs.Tab value="calendar">Calendar</Tabs.Tab>
          <Tabs.Tab value="animation">Animation</Tabs.Tab>
          <Tabs.Tab value="compare">Compare</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="audiogram" pt="md">
          <Stack gap="md">
            <Select
              label="Select Test"
              placeholder="Choose a test to view"
              data={tests.map(test => ({
                value: test.id,
                label: `${new Date(test.test_date).toLocaleDateString()} - ${test.location}`
              }))}
              value={selectedTestId}
              onChange={setSelectedTestId}
              searchable
            />

            {testLoading && (
              <Stack align="center" py="md">
                <Loader size="sm" />
              </Stack>
            )}

            {selectedTest && (
              <AudiogramChart
                leftEar={selectedTest.left_ear}
                rightEar={selectedTest.right_ear}
              />
            )}
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value="trends" pt="md">
          <FrequencyTrendChart
            tests={tests}
            getTestMeasurements={getTestMeasurements}
          />
        </Tabs.Panel>

        <Tabs.Panel value="calendar" pt="md">
          <TestCalendarHeatmap
            tests={tests}
            onTestClick={(testId) => {
              setSelectedTestId(testId)
              setActiveTab('audiogram')
            }}
          />
        </Tabs.Panel>

        <Tabs.Panel value="animation" pt="md">
          {allTestDetails ? (
            <AudiogramAnimation tests={allTestDetails} />
          ) : (
            <Stack align="center" py="md">
              <Loader size="sm" />
              <Text size="sm" c="dimmed">Loading test data...</Text>
            </Stack>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="compare" pt="md">
          {allTestDetails ? (
            <ComparisonGrid tests={allTestDetails} />
          ) : (
            <Stack align="center" py="md">
              <Loader size="sm" />
              <Text size="sm" c="dimmed">Loading test data...</Text>
            </Stack>
          )}
        </Tabs.Panel>
      </Tabs>
    </Stack>
  )
}
