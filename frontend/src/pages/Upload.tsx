import { Container, Title, Paper } from '@mantine/core'
import { UploadForm } from '../components/UploadForm'

export function Upload() {
  return (
    <Container size="md" py="xl">
      <Title order={1} mb="xl">Upload Hearing Test</Title>
      <Paper shadow="sm" p="md" withBorder>
        <UploadForm />
      </Paper>
    </Container>
  )
}
