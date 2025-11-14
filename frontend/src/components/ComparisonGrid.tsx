import { SimpleGrid, Stack, Text, Checkbox, Group, Paper } from '@mantine/core'
import { useState, useMemo } from 'react'
import { HearingTestDetail } from '../lib/api'
import { AudiogramChart } from './AudiogramChart'

interface ComparisonGridProps {
  tests: HearingTestDetail[]
}

export function ComparisonGrid({ tests }: ComparisonGridProps) {
  const [selectedTestIds, setSelectedTestIds] = useState<string[]>([])

  // Sort tests by date (most recent first)
  const sortedTests = useMemo(() => {
    return [...tests].sort((a, b) =>
      new Date(b.test_date).getTime() - new Date(a.test_date).getTime()
    )
  }, [tests])

  const selectedTests = useMemo(() => {
    return sortedTests.filter(test => selectedTestIds.includes(test.id))
  }, [sortedTests, selectedTestIds])

  const handleTestToggle = (testId: string) => {
    setSelectedTestIds(prev => {
      if (prev.includes(testId)) {
        return prev.filter(id => id !== testId)
      } else {
        // Limit to 4 tests
        if (prev.length >= 4) {
          return [...prev.slice(1), testId]
        }
        return [...prev, testId]
      }
    })
  }

  return (
    <Stack gap="lg">
      {/* Test selector */}
      <div>
        <Text size="sm" fw={500} mb="xs">
          Select tests to compare (up to 4):
        </Text>
        <Stack gap="xs">
          {sortedTests.length === 0 ? (
            <Text size="sm" c="dimmed">
              No tests available. Upload audiograms to enable comparison.
            </Text>
          ) : (
            sortedTests.map(test => (
              <Checkbox
                key={test.id}
                label={
                  <Group gap="xs">
                    <Text size="sm">
                      {new Date(test.test_date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </Text>
                    <Text size="xs" c="dimmed">
                      • {test.location}
                    </Text>
                  </Group>
                }
                checked={selectedTestIds.includes(test.id)}
                onChange={() => handleTestToggle(test.id)}
                disabled={!selectedTestIds.includes(test.id) && selectedTestIds.length >= 4}
              />
            ))
          )}
        </Stack>
      </div>

      {/* Comparison grid */}
      {selectedTests.length === 0 ? (
        <Paper p="xl" withBorder>
          <Text size="sm" c="dimmed" ta="center">
            Select tests above to compare them side-by-side
          </Text>
        </Paper>
      ) : (
        <SimpleGrid
          cols={{ base: 1, sm: 2 }}
          spacing="lg"
        >
          {selectedTests.map(test => (
            <Paper key={test.id} p="md" withBorder>
              <Stack gap="md">
                <div>
                  <Text size="md" fw={500}>
                    {new Date(test.test_date).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </Text>
                  <Text size="sm" c="dimmed">
                    {test.location} • {test.source_type}
                  </Text>
                </div>

                <AudiogramChart
                  leftEar={test.left_ear}
                  rightEar={test.right_ear}
                />
              </Stack>
            </Paper>
          ))}
        </SimpleGrid>
      )}

      {/* Change summary */}
      {selectedTests.length >= 2 && (
        <Paper p="md" withBorder>
          <Text size="sm" fw={500} mb="xs">Quick Comparison:</Text>
          <Stack gap="xs">
            <Group justify="apart">
              <Text size="sm">Earliest test:</Text>
              <Text size="sm" fw={500}>
                {new Date(selectedTests[selectedTests.length - 1].test_date).toLocaleDateString()}
              </Text>
            </Group>
            <Group justify="apart">
              <Text size="sm">Most recent test:</Text>
              <Text size="sm" fw={500}>
                {new Date(selectedTests[0].test_date).toLocaleDateString()}
              </Text>
            </Group>
            <Group justify="apart">
              <Text size="sm">Time span:</Text>
              <Text size="sm" fw={500}>
                {Math.round(
                  (new Date(selectedTests[0].test_date).getTime() -
                    new Date(selectedTests[selectedTests.length - 1].test_date).getTime()) /
                  (1000 * 60 * 60 * 24)
                )} days
              </Text>
            </Group>
          </Stack>
        </Paper>
      )}
    </Stack>
  )
}
