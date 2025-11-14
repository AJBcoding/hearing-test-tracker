import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Stack, Switch, Text } from '@mantine/core'
import { useState, useMemo } from 'react'
import { AudiogramMeasurement } from '../lib/api'

interface AudiogramChartProps {
  leftEar: AudiogramMeasurement[]
  rightEar: AudiogramMeasurement[]
  testDate?: string
}

const STANDARD_FREQUENCIES = [64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

// Hearing loss severity zones
const HEARING_ZONES = [
  { name: 'Normal', max: 25, color: '#e8f5e9' },
  { name: 'Mild', max: 40, color: '#fff9c4' },
  { name: 'Moderate', max: 55, color: '#ffe0b2' },
  { name: 'Severe', max: 70, color: '#ffcdd2' },
  { name: 'Profound', max: 120, color: '#ef9a9a' }
]

export function AudiogramChart({ leftEar, rightEar, testDate }: AudiogramChartProps) {
  const [showZones, setShowZones] = useState(true)

  // Prepare data for Recharts - combine both ears
  const chartData = useMemo(() => {
    return STANDARD_FREQUENCIES.map(freq => {
      const leftMeasurement = leftEar.find(m => m.frequency_hz === freq)
      const rightMeasurement = rightEar.find(m => m.frequency_hz === freq)

      return {
        frequency: freq,
        frequencyLabel: freq >= 1000 ? `${freq / 1000}k` : freq.toString(),
        left: leftMeasurement?.threshold_db ?? null,
        right: rightMeasurement?.threshold_db ?? null
      }
    })
  }, [leftEar, rightEar])

  const formatYAxis = (value: number) => `${value} dB`

  return (
    <Stack gap="md">
      <Switch
        label="Show hearing loss zones"
        checked={showZones}
        onChange={(e) => setShowZones(e.currentTarget.checked)}
      />

      {testDate && (
        <Text size="sm" c="dimmed">Test Date: {new Date(testDate).toLocaleDateString()}</Text>
      )}

      <ResponsiveContainer width="100%" height={500}>
        <LineChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" />

          {/* X-axis: Frequencies (logarithmic scale appearance) */}
          <XAxis
            dataKey="frequencyLabel"
            label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -10 }}
          />

          {/* Y-axis: Hearing threshold in dB (inverted) */}
          <YAxis
            reversed
            domain={[0, 120]}
            ticks={[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]}
            tickFormatter={formatYAxis}
            label={{ value: 'Hearing Level (dB HL)', angle: -90, position: 'insideLeft' }}
          />

          {/* Hearing loss zones as reference areas */}
          {showZones && HEARING_ZONES.map((zone) => (
            <ReferenceLine
              key={zone.name}
              y={zone.max}
              stroke="#999"
              strokeDasharray="3 3"
              strokeOpacity={0.3}
            />
          ))}

          <Tooltip
            formatter={(value: any) => {
              if (value === null || value === undefined) return 'No data'
              return `${Number(value).toFixed(1)} dB HL`
            }}
            labelFormatter={(label) => `Frequency: ${label} Hz`}
          />

          <Legend />

          {/* Right ear: Red line with circles */}
          <Line
            type="monotone"
            dataKey="right"
            stroke="#ef5350"
            strokeWidth={2}
            name="Right Ear"
            dot={{ fill: '#ef5350', r: 6 }}
            connectNulls={false}
          />

          {/* Left ear: Blue line with X markers */}
          <Line
            type="monotone"
            dataKey="left"
            stroke="#2196f3"
            strokeWidth={2}
            name="Left Ear"
            dot={{ fill: '#2196f3', r: 6 }}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Legend for hearing zones */}
      {showZones && (
        <Stack gap="xs">
          <Text size="sm" fw={500}>Hearing Loss Categories:</Text>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {HEARING_ZONES.map(zone => (
              <div key={zone.name} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{
                  width: 20,
                  height: 20,
                  backgroundColor: zone.color,
                  border: '1px solid #ccc'
                }} />
                <Text size="sm">{zone.name} (≤{zone.max} dB)</Text>
              </div>
            ))}
          </div>
        </Stack>
      )}
    </Stack>
  )
}
