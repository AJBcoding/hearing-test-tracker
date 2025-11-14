import { Container, Title, Paper, Tabs, Stack } from '@mantine/core'
import { UploadForm } from './components/UploadForm'
import { AudiogramViewer } from './components/AudiogramViewer'

export default function App() {
  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="xl">Hearing Test Tracker</Title>

      <Stack gap="xl">
        <Paper shadow="sm" p="md" withBorder>
          <Tabs defaultValue="upload">
            <Tabs.List>
              <Tabs.Tab value="upload">Upload</Tabs.Tab>
              <Tabs.Tab value="visualize">Visualize</Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="upload" pt="md">
              <UploadForm />
            </Tabs.Panel>

            <Tabs.Panel value="visualize" pt="md">
              <AudiogramViewer />
            </Tabs.Panel>
          </Tabs>
        </Paper>
      </Stack>
    </Container>
  )
}
