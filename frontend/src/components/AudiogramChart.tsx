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
          dot={{ fill: '#0000ff', r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
