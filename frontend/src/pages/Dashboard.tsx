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
