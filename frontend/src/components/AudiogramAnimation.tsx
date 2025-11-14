import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Button, Group, Stack, Text, Slider } from '@mantine/core'
import { useState, useMemo, useEffect } from 'react'
import { HearingTestDetail, AudiogramMeasurement } from '../lib/api'

interface AudiogramAnimationProps {
  tests: HearingTestDetail[]
}

const STANDARD_FREQUENCIES = [64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

export function AudiogramAnimation({ tests }: AudiogramAnimationProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)

  // Sort tests by date
  const sortedTests = useMemo(() => {
    return [...tests].sort((a, b) =>
      new Date(a.test_date).getTime() - new Date(b.test_date).getTime()
    )
  }, [tests])

  const currentTest = sortedTests[currentIndex]

  // Prepare chart data for current test
  const chartData = useMemo(() => {
    if (!currentTest) return []

    return STANDARD_FREQUENCIES.map(freq => {
      const leftMeasurement = currentTest.left_ear.find((m: AudiogramMeasurement) => m.frequency_hz === freq)
      const rightMeasurement = currentTest.right_ear.find((m: AudiogramMeasurement) => m.frequency_hz === freq)

      return {
        frequency: freq,
        frequencyLabel: freq >= 1000 ? `${freq / 1000}k` : freq.toString(),
        left: leftMeasurement?.threshold_db ?? null,
        right: rightMeasurement?.threshold_db ?? null
      }
    })
  }, [currentTest])

  // Animation playback
  useEffect(() => {
    if (!isPlaying) return

    const interval = setInterval(() => {
      setCurrentIndex(prev => {
        if (prev >= sortedTests.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 1000 / speed)

    return () => clearInterval(interval)
  }, [isPlaying, speed, sortedTests.length])

  const handlePlayPause = () => {
    if (currentIndex >= sortedTests.length - 1) {
      setCurrentIndex(0)
    }
    setIsPlaying(!isPlaying)
  }

  const handleSliderChange = (value: number) => {
    setCurrentIndex(value)
    setIsPlaying(false)
  }

  if (!currentTest) {
    return (
      <Stack align="center" justify="center" py="xl">
        <Text size="sm" c="dimmed">
          No tests available for animation. Upload at least 2 tests to see progression.
        </Text>
      </Stack>
    )
  }

  return (
    <Stack gap="md">
      {/* Current test info */}
      <Group justify="apart">
        <div>
          <Text size="lg" fw={500}>
            {new Date(currentTest.test_date).toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric'
            })}
          </Text>
          <Text size="sm" c="dimmed">
            Test {currentIndex + 1} of {sortedTests.length} • {currentTest.location}
          </Text>
        </div>
      </Group>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="frequencyLabel"
            label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -10 }}
          />

          <YAxis
            reversed
            domain={[0, 120]}
            label={{ value: 'Hearing Level (dB HL)', angle: -90, position: 'insideLeft' }}
          />

          <Tooltip
            formatter={(value: any) => {
              if (value === null || value === undefined) return 'No data'
              return `${Number(value).toFixed(1)} dB HL`
            }}
          />

          <Legend />

          <Line
            type="monotone"
            dataKey="right"
            stroke="#ef5350"
            strokeWidth={2}
            name="Right Ear"
            dot={{ fill: '#ef5350', r: 6 }}
            connectNulls={false}
            animationDuration={300}
          />

          <Line
            type="monotone"
            dataKey="left"
            stroke="#2196f3"
            strokeWidth={2}
            name="Left Ear"
            dot={{ fill: '#2196f3', r: 6 }}
            connectNulls={false}
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Playback controls */}
      <Stack gap="sm">
        <Slider
          value={currentIndex}
          onChange={handleSliderChange}
          min={0}
          max={Math.max(0, sortedTests.length - 1)}
          step={1}
          marks={sortedTests.map((test, idx) => ({
            value: idx,
            label: idx % Math.ceil(sortedTests.length / 5) === 0
              ? new Date(test.test_date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
              : ''
          }))}
          disabled={sortedTests.length < 2}
        />

        <Group justify="center" gap="md">
          <Button
            onClick={handlePlayPause}
            disabled={sortedTests.length < 2}
          >
            {isPlaying ? 'Pause' : currentIndex >= sortedTests.length - 1 ? 'Replay' : 'Play'}
          </Button>

          <Group gap="xs">
            <Text size="sm">Speed:</Text>
            {[0.5, 1, 2, 5].map(s => (
              <Button
                key={s}
                size="xs"
                variant={speed === s ? 'filled' : 'outline'}
                onClick={() => setSpeed(s)}
              >
                {s}x
              </Button>
            ))}
          </Group>
        </Group>
      </Stack>

      {sortedTests.length < 2 && (
        <Text size="sm" c="dimmed" ta="center">
          Upload more tests to enable animation playback
        </Text>
      )}
    </Stack>
  )
}
