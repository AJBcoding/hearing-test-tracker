import { Container, Title, Paper } from '@mantine/core'
import { UploadForm } from './components/UploadForm'

export default function App() {
  return (
    <Container size="md" py="xl">
      <Title order={1} mb="xl">Hearing Test Tracker</Title>

      <Paper shadow="sm" p="md" withBorder>
        <UploadForm />
      </Paper>
    </Container>
  )
}
