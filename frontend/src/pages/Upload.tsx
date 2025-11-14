import { Container, Title, Tabs } from '@mantine/core'
import { IconUpload, IconFolderOpen } from '@tabler/icons-react'
import { UploadForm } from '../components/UploadForm'
import { BulkUploadForm } from '../components/BulkUploadForm'

export function Upload() {
  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="xl">Upload Hearing Test</Title>

      <Tabs defaultValue="single" variant="pills">
        <Tabs.List mb="md">
          <Tabs.Tab value="single" leftSection={<IconUpload size={16} />}>
            Single Upload
          </Tabs.Tab>
          <Tabs.Tab value="bulk" leftSection={<IconFolderOpen size={16} />}>
            Bulk Upload
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="single">
          <UploadForm />
        </Tabs.Panel>

        <Tabs.Panel value="bulk">
          <BulkUploadForm />
        </Tabs.Panel>
      </Tabs>
    </Container>
  )
}
