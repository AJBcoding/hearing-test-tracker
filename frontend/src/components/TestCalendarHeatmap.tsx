import { Stack, Text, Group, Badge } from '@mantine/core'
import { useMemo } from 'react'
import { HearingTest } from '../lib/api'

interface TestCalendarHeatmapProps {
  tests: HearingTest[]
  onTestClick?: (testId: string) => void
}

export function TestCalendarHeatmap({ tests, onTestClick }: TestCalendarHeatmapProps) {
  const calendarData = useMemo(() => {
    if (!tests || tests.length === 0) return []

    // Group tests by month and year
    const testsByMonth: { [key: string]: HearingTest[] } = {}

    tests.forEach(test => {
      const date = new Date(test.test_date)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`

      if (!testsByMonth[monthKey]) {
        testsByMonth[monthKey] = []
      }
      testsByMonth[monthKey].push(test)
    })

    return Object.entries(testsByMonth)
      .sort((a, b) => b[0].localeCompare(a[0])) // Most recent first
      .map(([monthKey, monthTests]) => ({
        month: monthKey,
        tests: monthTests.sort((a, b) =>
          new Date(b.test_date).getTime() - new Date(a.test_date).getTime()
        )
      }))
  }, [tests])

  const getColorForConfidence = (confidence: number) => {
    if (confidence >= 0.9) return '#4caf50'
    if (confidence >= 0.8) return '#8bc34a'
    if (confidence >= 0.7) return '#ffeb3b'
    if (confidence >= 0.6) return '#ff9800'
    return '#f44336'
  }

  const formatMonthYear = (monthKey: string) => {
    const [year, month] = monthKey.split('-')
    const date = new Date(parseInt(year), parseInt(month) - 1)
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  }

  return (
    <Stack gap="lg">
      <Text size="sm" c="dimmed">
        {tests.length} test{tests.length !== 1 ? 's' : ''} across {calendarData.length} month{calendarData.length !== 1 ? 's' : ''}
      </Text>

      {calendarData.length === 0 ? (
        <Text size="sm" c="dimmed" ta="center" py="xl">
          No tests available. Upload your first audiogram to get started.
        </Text>
      ) : (
        <Stack gap="xl">
          {calendarData.map(({ month, tests: monthTests }) => (
            <div key={month}>
              <Text size="md" fw={500} mb="md">{formatMonthYear(month)}</Text>
              <Stack gap="xs">
                {monthTests.map(test => (
                  <div
                    key={test.id}
                    onClick={() => onTestClick?.(test.id)}
                    style={{
                      padding: '12px',
                      backgroundColor: '#f8f9fa',
                      borderLeft: `4px solid ${getColorForConfidence(test.confidence)}`,
                      borderRadius: '4px',
                      cursor: onTestClick ? 'pointer' : 'default',
                      transition: 'background-color 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      if (onTestClick) {
                        e.currentTarget.style.backgroundColor = '#e9ecef'
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#f8f9fa'
                    }}
                  >
                    <Group justify="apart">
                      <div>
                        <Text size="sm" fw={500}>
                          {new Date(test.test_date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </Text>
                        <Text size="xs" c="dimmed">{test.location}</Text>
                      </div>
                      <Group gap="xs">
                        <Badge size="sm" variant="light" color={test.source_type === 'audiologist' ? 'blue' : 'green'}>
                          {test.source_type}
                        </Badge>
                        <Badge
                          size="sm"
                          color={test.confidence >= 0.8 ? 'green' : 'yellow'}
                        >
                          {Math.round(test.confidence * 100)}%
                        </Badge>
                      </Group>
                    </Group>
                  </div>
                ))}
              </Stack>
            </div>
          ))}
        </Stack>
      )}

      {/* Legend */}
      <div>
        <Text size="sm" fw={500} mb="xs">OCR Confidence:</Text>
        <Group gap="md">
          {[
            { label: 'Excellent (90%+)', color: '#4caf50' },
            { label: 'Good (80-89%)', color: '#8bc34a' },
            { label: 'Fair (70-79%)', color: '#ffeb3b' },
            { label: 'Poor (60-69%)', color: '#ff9800' },
            { label: 'Low (<60%)', color: '#f44336' }
          ].map(item => (
            <Group key={item.label} gap="xs">
              <div style={{
                width: 16,
                height: 16,
                backgroundColor: item.color,
                borderRadius: '2px'
              }} />
              <Text size="xs">{item.label}</Text>
            </Group>
          ))}
        </Group>
      </div>
    </Stack>
  )
}
