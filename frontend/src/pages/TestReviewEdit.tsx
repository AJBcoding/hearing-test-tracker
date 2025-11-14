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
