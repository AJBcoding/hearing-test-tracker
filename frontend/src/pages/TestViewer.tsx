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
