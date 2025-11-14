import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Button, Group, Stack, Text } from '@mantine/core'
import { useState, useMemo } from 'react'
import { HearingTest } from '../lib/api'

interface FrequencyTrendChartProps {
  tests: HearingTest[]
  getTestMeasurements: (testId: string) => { left: number | null, right: number | null }
}

const FREQUENCIES = [125, 250, 500, 1000, 2000, 4000, 8000]

export function FrequencyTrendChart({ tests, getTestMeasurements }: FrequencyTrendChartProps) {
  const [selectedFrequency, setSelectedFrequency] = useState(1000)

  // Prepare time-series data for selected frequency
  const chartData = useMemo(() => {
    if (!tests || tests.length === 0) return []

    // Sort tests by date
    const sortedTests = [...tests].sort((a, b) =>
      new Date(a.test_date).getTime() - new Date(b.test_date).getTime()
    )

    return sortedTests.map(test => {
      const measurements = getTestMeasurements(test.id)

      return {
        date: new Date(test.test_date).toLocaleDateString(),
        fullDate: test.test_date,
        left: measurements.left,
        right: measurements.right,
        location: test.location,
        sourceType: test.source_type
      }
    })
  }, [tests, selectedFrequency, getTestMeasurements])

  return (
    <Stack gap="md">
      <div>
        <Text size="sm" fw={500} mb="xs">Select Frequency:</Text>
        <Group gap="xs">
          {FREQUENCIES.map(freq => (
            <Button
              key={freq}
              size="xs"
              variant={selectedFrequency === freq ? 'filled' : 'outline'}
              onClick={() => setSelectedFrequency(freq)}
            >
              {freq >= 1000 ? `${freq / 1000}k Hz` : `${freq} Hz`}
            </Button>
          ))}
        </Group>
      </div>

      <Text size="sm" c="dimmed">
        Tracking: {selectedFrequency >= 1000 ? `${selectedFrequency / 1000}k Hz` : `${selectedFrequency} Hz`}
        {' '}over {chartData.length} test{chartData.length !== 1 ? 's' : ''}
      </Text>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="date"
            label={{ value: 'Test Date', position: 'insideBottom', offset: -10 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />

          <YAxis
            reversed
            domain={[0, 120]}
            label={{ value: 'Hearing Threshold (dB HL)', angle: -90, position: 'insideLeft' }}
          />

          <Tooltip
            formatter={(value: any) => {
              if (value === null || value === undefined) return 'No data'
              return `${Number(value).toFixed(1)} dB HL`
            }}
            labelFormatter={(label, payload) => {
              if (payload && payload[0]) {
                const data = payload[0].payload
                return `${label} (${data.sourceType})`
              }
              return label
            }}
          />

          <Legend />

          <Line
            type="monotone"
            dataKey="right"
            stroke="#ef5350"
            strokeWidth={2}
            name="Right Ear"
            dot={{ fill: '#ef5350', r: 5 }}
            connectNulls={false}
          />

          <Line
            type="monotone"
            dataKey="left"
            stroke="#2196f3"
            strokeWidth={2}
            name="Left Ear"
            dot={{ fill: '#2196f3', r: 5 }}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>

      {chartData.length < 2 && (
        <Text size="sm" c="dimmed" ta="center">
          Add more tests to see trends over time
        </Text>
      )}
    </Stack>
  )
}
