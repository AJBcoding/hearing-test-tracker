import { Container, Title, Table, Button, Badge, Group } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { listTests } from '../lib/api'

export function TestList() {
  const navigate = useNavigate()
  const { data: tests = [], isLoading } = useQuery({
    queryKey: ['tests'],
    queryFn: listTests
  })

  if (isLoading) {
    return <Container><Title>Loading...</Title></Container>
  }

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <div>
          <Title order={1}>All Tests</Title>
          <Title order={4} c="dimmed" fw={400}>
            Showing {tests.length} test{tests.length !== 1 ? 's' : ''}
          </Title>
        </div>
        <Button onClick={() => navigate('/upload')}>
          Upload New Test
        </Button>
      </Group>

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Date</Table.Th>
            <Table.Th>Location</Table.Th>
            <Table.Th>Source</Table.Th>
            <Table.Th>Device</Table.Th>
            <Table.Th>Confidence</Table.Th>
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {tests.map((test) => (
            <Table.Tr
              key={test.id}
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/tests/${test.id}`)}
            >
              <Table.Td>{new Date(test.test_date).toLocaleDateString()}</Table.Td>
              <Table.Td>{test.location}</Table.Td>
              <Table.Td>{test.source_type}</Table.Td>
              <Table.Td>{test.id}</Table.Td>
              <Table.Td>
                <Badge color={test.confidence >= 0.8 ? 'green' : 'yellow'}>
                  {(test.confidence * 100).toFixed(0)}%
                </Badge>
              </Table.Td>
              <Table.Td onClick={(e) => e.stopPropagation()}>
                <Button
                  size="xs"
                  variant="light"
                  onClick={() => navigate(`/tests/${test.id}`)}
                >
                  View
                </Button>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Container>
  )
}
