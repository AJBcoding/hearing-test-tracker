import { useState } from 'react'
import {
  Button,
  FileInput,
  Stack,
  Alert,
  Progress,
  Table,
  Text,
  Group,
  Badge,
  Paper,
  Title
} from '@mantine/core'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notifications } from '@mantine/notifications'
import { IconUpload, IconCheck, IconX, IconAlertCircle } from '@tabler/icons-react'
import { bulkUploadAudiograms, BulkUploadResult } from '../lib/api'

export function BulkUploadForm() {
  const [files, setFiles] = useState<File[]>([])
  const [results, setResults] = useState<BulkUploadResult[] | null>(null)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: bulkUploadAudiograms,
    onSuccess: (data) => {
      setResults(data.results)

      notifications.show({
        title: 'Bulk Upload Complete',
        message: `Successfully uploaded ${data.successful} of ${data.total} files`,
        color: data.failed === 0 ? 'green' : 'yellow'
      })

      queryClient.invalidateQueries({ queryKey: ['tests'] })

      // Clear files after successful upload
      setFiles([])
    },
    onError: (error) => {
      notifications.show({
        title: 'Bulk Upload Failed',
        message: error.message,
        color: 'red'
      })
    }
  })

  const handleUpload = () => {
    if (files.length > 0) {
      setResults(null) // Clear previous results
      uploadMutation.mutate(files)
    }
  }

  const handleClearResults = () => {
    setResults(null)
  }

  return (
    <Stack gap="lg">
      <Paper p="md" withBorder>
        <Stack>
          <Title order={3}>Bulk Upload Audiograms</Title>

          <FileInput
            label="Select Multiple Audiogram Images"
            placeholder="Click to select multiple JPEG files"
            accept="image/jpeg,image/jpg,image/png"
            multiple
            value={files}
            onChange={setFiles}
            description={`${files.length} file(s) selected`}
          />

          <Group>
            <Button
              onClick={handleUpload}
              disabled={files.length === 0 || uploadMutation.isPending}
              loading={uploadMutation.isPending}
              leftSection={<IconUpload size={16} />}
            >
              Upload {files.length} File{files.length !== 1 ? 's' : ''}
            </Button>

            {files.length > 0 && (
              <Button
                variant="outline"
                onClick={() => setFiles([])}
                disabled={uploadMutation.isPending}
              >
                Clear Selection
              </Button>
            )}
          </Group>

          {uploadMutation.isPending && (
            <Stack gap="xs">
              <Text size="sm" c="dimmed">
                Processing files, please wait...
              </Text>
              <Progress value={100} animated />
            </Stack>
          )}
        </Stack>
      </Paper>

      {uploadMutation.isError && (
        <Alert
          color="red"
          title="Upload Failed"
          icon={<IconX size={16} />}
        >
          {uploadMutation.error.message}
        </Alert>
      )}

      {results && results.length > 0 && (
        <Paper p="md" withBorder>
          <Stack gap="md">
            <Group justify="space-between">
              <Title order={4}>Upload Results</Title>
              <Button
                variant="subtle"
                size="sm"
                onClick={handleClearResults}
              >
                Clear Results
              </Button>
            </Group>

            <Group>
              <Badge color="green" size="lg">
                {results.filter(r => r.status === 'success').length} Successful
              </Badge>
              <Badge color="red" size="lg">
                {results.filter(r => r.status === 'error').length} Failed
              </Badge>
            </Group>

            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Filename</Table.Th>
                  <Table.Th>Confidence</Table.Th>
                  <Table.Th>Review Needed</Table.Th>
                  <Table.Th>Details</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {results.map((result, index) => (
                  <Table.Tr key={index}>
                    <Table.Td>
                      {result.status === 'success' ? (
                        <IconCheck size={20} color="green" />
                      ) : (
                        <IconX size={20} color="red" />
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{result.filename}</Text>
                    </Table.Td>
                    <Table.Td>
                      {result.confidence !== undefined ? (
                        <Text size="sm">
                          {(result.confidence * 100).toFixed(0)}%
                        </Text>
                      ) : (
                        <Text size="sm" c="dimmed">-</Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      {result.needs_review !== undefined ? (
                        result.needs_review ? (
                          <Badge color="yellow" leftSection={<IconAlertCircle size={12} />}>
                            Review
                          </Badge>
                        ) : (
                          <Badge color="green">
                            OK
                          </Badge>
                        )
                      ) : (
                        <Text size="sm" c="dimmed">-</Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      {result.status === 'success' && result.test_id ? (
                        <Button
                          component="a"
                          href={`/tests/${result.test_id}`}
                          size="xs"
                          variant="subtle"
                        >
                          View Test
                        </Button>
                      ) : (
                        <Text size="xs" c="red">
                          {result.error}
                        </Text>
                      )}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Stack>
        </Paper>
      )}
    </Stack>
  )
}
